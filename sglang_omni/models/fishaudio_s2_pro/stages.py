# SPDX-License-Identifier: Apache-2.0
"""Stage factories for Fish Audio S2-Pro TTS pipeline.

Each factory returns a callable (for SimpleScheduler) or an OmniScheduler.
"""

from __future__ import annotations

import base64
import ctypes
import logging
import os
import threading
import time
from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

import torch
from dac.nn.layers import Snake1d

from sglang_omni.models.fishaudio_s2_pro.fish_speech.models.dac.modded_dac import (
    CausalConvNet,
    get_extra_padding_for_conv1d,
)
from sglang_omni.models.fishaudio_s2_pro.payload_types import S2ProState
from sglang_omni.preprocessing.audio import decode_audio_bytes_av, parse_wav_bytes
from sglang_omni.preprocessing.cache_key import hash_bytes as _hash_bytes
from sglang_omni.preprocessing.cache_key import (
    reference_path_cache_key as _reference_path_cache_key,
)
from sglang_omni.proto import StagePayload
from sglang_omni.scheduling.pipeline_state import load_state as _load_pipeline_state
from sglang_omni.scheduling.pipeline_state import store_state as _store_pipeline_state
from sglang_omni.scheduling.reference_encoder import (
    ReferenceEncodeKey,
    ReferenceEncodeService,
    TensorReferenceEncodeHook,
)
from sglang_omni.utils.audio import load_audio
from sglang_omni.utils.checkpoint import resolve_checkpoint as _resolve_checkpoint

if TYPE_CHECKING:
    from sglang_omni.models.fishaudio_s2_pro.fish_speech.models.dac.modded_dac import (
        DAC,
    )
    from sglang_omni.models.fishaudio_s2_pro.sglang_model import S2ProSGLangTextModel
else:
    pass

logger = logging.getLogger(__name__)

_MAX_PREPROCESSING_INTRAOP_THREADS = 8
PREPROCESSING_THREAD_BUDGET_MULTIPLIER = 2
REFERENCE_SNAKE_EPSILON = 1e-9
REFERENCE_MMAP_THRESHOLD_BYTES = 64 * 1024 * 1024
GLIBC_M_MMAP_THRESHOLD = -3
REFERENCE_ACTIVATION_VECTOR_ELEMENTS = 16


def configure_preprocessing_threads(worker_count: int) -> int:
    override = os.environ.get("OMP_NUM_THREADS", "").strip()
    from_cpu_plan = os.environ.get("SGLANG_OMNI_OMP_FROM_CPU_PLAN") == "1"
    if override.isdigit() and int(override) >= 1:
        if not from_cpu_plan:
            requested = int(override)
            torch.set_num_threads(requested)
            return requested
        else:
            cpu_count = int(override)
    else:
        cpu_count = (
            len(os.sched_getaffinity(0))
            if hasattr(os, "sched_getaffinity")
            else (os.cpu_count() or 1)
        )
    # note (Zhuofeng-Li): coalesced reference waiters leave CPU capacity for encoders.
    intraop_threads = min(
        max(cpu_count * PREPROCESSING_THREAD_BUDGET_MULTIPLIER // worker_count, 1),
        _MAX_PREPROCESSING_INTRAOP_THREADS,
    )
    torch.set_num_threads(intraop_threads)
    return intraop_threads


def warmup_s2pro_codebook_decoder(
    model: "S2ProSGLangTextModel", *, max_batch_size: int
) -> None:
    """Materialize Fast AR compile variants before serving real requests."""
    if max_batch_size < 1:
        raise ValueError("max_batch_size must be >= 1")
    else:
        pass

    audio_decoder = model.audio_decoder
    embedding_weight = audio_decoder.embeddings.weight
    hidden_size = int(embedding_weight.shape[1])
    batch_sizes = sorted(
        batch_size
        for batch_size in {1, 2, 4, 8, 16, 32, max_batch_size}
        if batch_size <= max_batch_size
    )
    warmup_input = torch.zeros(
        (max_batch_size, 1, hidden_size),
        device=embedding_weight.device,
        dtype=embedding_weight.dtype,
    )
    num_codebooks = int(audio_decoder.config.num_codebooks)

    audio_decoder.reset_caches()
    try:
        with torch.no_grad():
            for _ in range(2):
                for batch_size in batch_sizes:
                    decoder_input = warmup_input[:batch_size]
                    for codebook_idx in range(num_codebooks):
                        audio_decoder.forward_kvcached(
                            decoder_input,
                            codebook_idx=codebook_idx,
                        )
    finally:
        audio_decoder.reset_caches()
        if embedding_weight.device.type == "cuda":
            torch.cuda.synchronize(embedding_weight.device)
        else:
            pass


def compile_s2pro_codebook_decoder(
    model: "S2ProSGLangTextModel", *, max_batch_size: int
) -> None:
    """Compile and warm Fast AR layers, falling back to eager on warmup failure."""
    from sglang.srt.compilation.torch_compile_decoration import set_torch_compile_config

    if max_batch_size < 1:
        raise ValueError("max_batch_size must be >= 1")
    else:
        pass

    set_torch_compile_config()
    compile_mode = os.environ.get(
        "SGLANG_TORCH_COMPILE_MODE",
        "max-autotune-no-cudagraphs",
    )
    audio_decoder = model.audio_decoder
    setup_start = time.perf_counter()
    compiled_forward_kvcached_layers = [
        torch.compile(layer.forward_kvcached, mode=compile_mode, dynamic=True)
        for layer in audio_decoder.layers
    ]
    audio_decoder.set_compiled_forward_kvcached_layers(
        compiled_forward_kvcached_layers,
        max_batch_size=max_batch_size,
    )
    setup_seconds = time.perf_counter() - setup_start
    warmup_start = time.perf_counter()
    try:
        warmup_s2pro_codebook_decoder(model, max_batch_size=max_batch_size)
    except Exception:
        audio_decoder.compiled_forward_kvcached_layers = None
        audio_decoder.compiled_forward_kvcached_max_bs = 0
        audio_decoder.reset_caches()
        logger.exception(
            "Fish S2-Pro Fast AR compile warmup failed; continuing with eager layers"
        )
        return
    warmup_seconds = time.perf_counter() - warmup_start
    logger.info(
        "Compiled and warmed %d Fast AR decoder layers "
        "(mode=%s, max_batch_size=%d, setup=%.2fs, warmup=%.2fs)",
        len(compiled_forward_kvcached_layers),
        compile_mode,
        max_batch_size,
        setup_seconds,
        warmup_seconds,
    )


def resolve_s2pro_model_buffer_bs(model: "S2ProSGLangTextModel") -> int:
    return min(
        int(model.vq_decode_max_batch_size),
        int(model.audio_decoder.kv_cache_max_batch_size),
    )


def load_codec(checkpoint_dir: str, device: str) -> "DAC":
    from hydra.utils import instantiate
    from omegaconf import OmegaConf

    OmegaConf.register_new_resolver("eval", eval, replace=True)
    codec_path = os.path.join(checkpoint_dir, "codec.pth")
    import sglang_omni.models.fishaudio_s2_pro.fish_speech.models.dac.modded_dac as _dac_mod

    configs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(_dac_mod.__file__))),
        "configs",
    )
    cfg = OmegaConf.load(os.path.join(configs_dir, "modded_dac_vq.yaml"))
    codec = instantiate(cfg)
    state_dict = torch.load(
        codec_path, map_location=device, mmap=True, weights_only=True
    )
    codec.load_state_dict(state_dict, strict=False, assign=True)
    codec.eval().to(device)
    return codec


def load_state(payload: StagePayload) -> S2ProState:
    return _load_pipeline_state(payload, S2ProState)


def store_state(payload: StagePayload, state: S2ProState) -> StagePayload:
    return _store_pipeline_state(payload, state)


@dataclass(frozen=True)
class FishReferenceInput:
    source_kind: str
    source: object
    media_type: str | None = None


def fish_reference_payload_is_supported(ref_data: Mapping[str, object]) -> bool:
    return (
        ref_data.get("audio_path") is not None
        or ref_data.get("bytes") is not None
        or ref_data.get("base64") is not None
        or ref_data.get("data") is not None
    )


class FishReferenceEncodeHook(TensorReferenceEncodeHook[FishReferenceInput]):
    model_id = "fishaudio_s2_pro"
    encoder_id = "fishaudio_s2_pro_codec"
    artifact_kind = "fishaudio_s2_pro_vq_codes"
    storage_dtype = torch.long
    output_dtype = torch.long

    def __init__(
        self,
        *,
        codec: "DAC",
        checkpoint_id: str,
        device: str = "cpu",
        autocast_dtype: torch.dtype | None = None,
        max_reference_audio_seconds: float | None = None,
    ) -> None:
        self.codec = codec
        self.device = torch.device(device)
        self.autocast_dtype = autocast_dtype
        self.max_reference_audio_seconds = max_reference_audio_seconds
        self.encode_lock = threading.Lock()
        self.model_revision = str(checkpoint_id)
        config = f"sample_rate:{int(codec.sample_rate)}"
        self.encoder_config_hash = _hash_bytes(config.encode("utf-8"))

    def normalize_input(self, raw_input: object) -> FishReferenceInput:
        if not isinstance(raw_input, dict):
            raise TypeError("FishAudio reference input must be a dict")
        else:
            pass
        if raw_input.get("audio_path") is not None:
            return FishReferenceInput("path", str(raw_input["audio_path"]))
        else:
            pass
        if raw_input.get("bytes") is not None:
            return FishReferenceInput("bytes", bytes(raw_input["bytes"]))
        else:
            pass
        data = raw_input.get("base64") or raw_input.get("data")
        if data is not None:
            return FishReferenceInput(
                "base64",
                data,
                str(raw_input.get("media_type") or "audio/wav"),
            )
        else:
            pass
        raise ValueError("FishAudio reference input has no audio payload")

    def encode_one(self, item: FishReferenceInput) -> torch.Tensor:
        if item.source_kind == "path":
            audio = load_audio(
                str(item.source),
                target_sample_rate=int(self.codec.sample_rate),
                mono=True,
            )
            audio_tensor = torch.from_numpy(audio).float().reshape(1, -1)
            return self.encode_reference_waveform(
                audio_tensor, int(self.codec.sample_rate)
            )
        else:
            pass
        if item.source_kind in ("bytes", "base64"):
            if item.source_kind == "bytes":
                assert isinstance(item.source, bytes)
                audio_bytes = item.source
            else:
                assert isinstance(item.source, str)
                audio_bytes = base64.b64decode(item.source)
            try:
                audio, sample_rate = parse_wav_bytes(audio_bytes, source="bytes")
            except ValueError:
                audio, sample_rate = decode_audio_bytes_av(audio_bytes)
            audio_tensor = torch.from_numpy(audio).float().reshape(1, -1)
            return self.encode_reference_waveform(audio_tensor, sample_rate)
        else:
            pass
        raise TypeError(f"unknown FishAudio reference source: {item.source_kind}")

    def revalidate(self, item: FishReferenceInput, key: ReferenceEncodeKey) -> bool:
        return item.source_kind != "path" or self.input_key(item) == key.input_key

    def input_key(self, item: FishReferenceInput) -> str | None:
        if item.source_kind == "path":
            return _reference_path_cache_key(str(item.source), trust_stat=False)
        else:
            pass
        if item.source_kind == "bytes":
            return f"bytes:{_hash_bytes(item.source)}"
        else:
            pass
        if item.source_kind == "base64":
            payload = str(item.source).encode("utf-8")
            media_type = item.media_type or "audio/wav"
            return f"base64:{media_type}:{_hash_bytes(payload)}"
        else:
            pass
        return None

    def encode_reference_waveform(self, audio: torch.Tensor, sr: int) -> torch.Tensor:
        import torchaudio

        if (
            self.max_reference_audio_seconds is not None
            and audio.shape[-1] > self.max_reference_audio_seconds * sr
        ):
            raise ValueError(
                f"reference audio lasts {audio.shape[-1] / sr:.1f} s, longer than "
                f"the {self.max_reference_audio_seconds:g} s limit; shorten it or "
                f"raise max_reference_audio_seconds"
            )
        else:
            pass
        if audio.shape[0] > 1:
            audio = audio.mean(0, keepdim=True)
        else:
            pass
        audio = torchaudio.functional.resample(audio, sr, self.codec.sample_rate)
        audios = audio.squeeze(0).unsqueeze(0)
        if self.autocast_dtype is not None:
            audios = audios.clamp(-1.0, 1.0)
        else:
            pass
        audio_lengths = torch.tensor([audios.shape[1]], dtype=torch.long)
        with (
            torch.no_grad(),
            torch.autocast(
                self.device.type,
                dtype=self.autocast_dtype,
                enabled=self.autocast_dtype is not None,
            ),
            self.encode_lock if self.device.type != "cpu" else nullcontext(),
        ):
            indices, _ = self.codec.encode(
                audios.to(self.device), audio_lengths.to(self.device)
            )
            if indices.ndim == 3:
                indices = indices[0]
            else:
                pass
        return indices.cpu()


def reuse_reference_activation(
    hidden_states: torch.Tensor, *, alpha: torch.Tensor
) -> torch.Tensor:
    original_shape = hidden_states.shape
    hidden_states = hidden_states.reshape(original_shape[0], original_shape[1], -1)
    # note (Zhuofeng-Li): mutate only a private temporary, preserving shared inputs.
    activation = alpha * hidden_states
    activation.sin_()
    activation.square_()
    activation.mul_((alpha + REFERENCE_SNAKE_EPSILON).reciprocal())
    activation.add_(hidden_states)
    return activation.reshape(original_shape)


@dataclass(frozen=True)
class ReferenceActivationPadding:
    padded: torch.Tensor
    consumer: CausalConvNet
    left_samples: int
    right_samples: int
    tensor_version: int


def produce_padded_reference_activation(
    hidden_states: torch.Tensor, *, alpha: torch.Tensor, consumer: CausalConvNet
) -> torch.Tensor:
    if (
        hidden_states.ndim != 3
        or hidden_states.device.type != "cpu"
        or hidden_states.dtype != torch.float32
        or alpha.dtype != hidden_states.dtype
        or not hidden_states.is_contiguous()
        or hidden_states.shape[-1] % REFERENCE_ACTIVATION_VECTOR_ELEMENTS
        or torch.is_grad_enabled()
        or torch.is_inference_mode_enabled()
        or consumer.training
        or consumer.padding <= 0
    ):
        return reuse_reference_activation(hidden_states, alpha=alpha)
    else:
        pass

    left_samples = consumer.padding
    right_samples = get_extra_padding_for_conv1d(
        hidden_states, consumer.kernel_size, consumer.stride, left_samples
    )
    input_samples = hidden_states.shape[-1]
    padded = torch.empty(
        (*hidden_states.shape[:-1], left_samples + input_samples + right_samples),
        device=hidden_states.device,
        dtype=hidden_states.dtype,
    )
    padded[..., :left_samples].zero_()
    if right_samples:
        padded[..., -right_samples:].zero_()
    else:
        pass
    activation = padded[..., left_samples : left_samples + input_samples]
    torch.mul(alpha, hidden_states, out=activation)
    activation.sin_()
    activation.square_()
    activation.mul_((alpha + REFERENCE_SNAKE_EPSILON).reciprocal())
    activation.add_(hidden_states)
    # note (Zhuofeng-Li): only the adjacent convolution can consume this owned storage.
    activation.fish_reference_padding = ReferenceActivationPadding(
        padded,
        consumer,
        left_samples,
        right_samples,
        activation._version,  # noqa: leading-underscore - PyTorch storage mutation counter.
    )
    return activation


def consume_padded_reference_activation(
    hidden_states: torch.Tensor, *, consumer: CausalConvNet
) -> torch.Tensor:
    padding = getattr(hidden_states, "fish_reference_padding", None)
    if (
        isinstance(padding, ReferenceActivationPadding)
        and padding.consumer is consumer
        and not torch.is_grad_enabled()
        and not torch.is_inference_mode_enabled()
        and not consumer.training
        and not consumer.conv._forward_pre_hooks  # noqa: leading-underscore - Preserve PyTorch module hook semantics.
        and not consumer.conv._forward_hooks  # noqa: leading-underscore - Preserve PyTorch module hook semantics.
        and not torch.nn.modules.module._global_forward_pre_hooks  # noqa: leading-underscore - Preserve PyTorch module hook semantics.
        and not torch.nn.modules.module._global_forward_hooks  # noqa: leading-underscore - Preserve PyTorch module hook semantics.
        and hidden_states._version
        == padding.tensor_version  # noqa: leading-underscore - PyTorch storage mutation counter.
        and padding.padded._version
        == padding.tensor_version  # noqa: leading-underscore - PyTorch storage mutation counter.
        and padding.left_samples == consumer.padding
        and padding.right_samples
        == get_extra_padding_for_conv1d(
            hidden_states, consumer.kernel_size, consumer.stride, consumer.padding
        )
    ):
        return consumer.conv(padding.padded).contiguous()
    else:
        return CausalConvNet.forward(consumer, hidden_states)


def create_preprocessing_executor(
    model_path: str,
    *,
    max_concurrency: int = 8,
):
    """Returns a threaded scheduler for CPU-heavy preprocessing."""
    from sglang_omni.scheduling.threaded_simple_scheduler import ThreadedSimpleScheduler

    worker_count = max(int(max_concurrency), 1)
    intraop_threads = configure_preprocessing_threads(worker_count)
    try:
        configure_allocator = ctypes.CDLL(None).mallopt
    except AttributeError:
        logger.info("Fish reference allocation retains the platform allocator policy")
    else:
        configure_allocator.argtypes = [ctypes.c_int, ctypes.c_int]
        configure_allocator.restype = ctypes.c_int
        # note (Zhuofeng-Li): reuse large CPU temporaries across reference encodes.
        allocator_configured = configure_allocator(
            GLIBC_M_MMAP_THRESHOLD, REFERENCE_MMAP_THRESHOLD_BYTES
        )
        logger.info(
            f"Fish reference allocator mmap threshold bytes={REFERENCE_MMAP_THRESHOLD_BYTES}, "
            f"configured={allocator_configured}"
        )
    logger.info(
        f"Fish preprocessing uses {worker_count} workers, {intraop_threads} shared intra-op threads"
    )
    checkpoint_dir = _resolve_checkpoint(model_path)

    from transformers import PreTrainedTokenizerFast

    from sglang_omni.models.fishaudio_s2_pro.tokenizer import (
        Reference,
        S2ProTokenizerAdapter,
    )

    tokenizer = PreTrainedTokenizerFast.from_pretrained(checkpoint_dir)
    adapter = S2ProTokenizerAdapter(tokenizer)
    codec = load_codec(checkpoint_dir, "cpu")
    activation_count = 0
    for activation in codec.encoder.modules():
        if isinstance(activation, Snake1d):
            activation.forward = partial(
                reuse_reference_activation, alpha=activation.alpha
            )
            activation_count += 1
        else:
            pass
    logger.info(
        f"Fish reference encoder private activation buffers: {activation_count}"
    )
    padding_pair_count = 0
    if torch.backends.cpu.get_cpu_capability() in ("AVX2", "AVX512"):
        for parent in codec.encoder.modules():
            if isinstance(parent, torch.nn.Sequential):
                children = list(parent.children())
                for producer, consumer in zip(children, children[1:]):
                    if (
                        isinstance(producer, Snake1d)
                        and isinstance(consumer, CausalConvNet)
                        and consumer.padding > 0
                    ):
                        producer.forward = partial(
                            produce_padded_reference_activation,
                            alpha=producer.alpha,
                            consumer=consumer,
                        )
                        consumer.forward = partial(
                            consume_padded_reference_activation, consumer=consumer
                        )
                        padding_pair_count += 1
                    else:
                        pass
            else:
                pass
    else:
        pass
    logger.info(f"Fish reference encoder owned padding pairs: {padding_pair_count}")
    reference_encode_service = ReferenceEncodeService(
        FishReferenceEncodeHook(codec=codec, checkpoint_id=checkpoint_dir),
        max_items=256,
        max_bytes=64 * 1024 * 1024,
        timeout_s=130.0,
        log_prefix="FishAudio S2-Pro",
    )

    def _preprocess(payload: StagePayload) -> StagePayload:
        inputs = payload.request.inputs or {}
        params = payload.request.params or {}
        if isinstance(inputs, str):
            inputs = {"text": inputs}
        else:
            pass

        text = inputs.get("text", "")
        num_codebooks = inputs.get("num_codebooks", 10)
        codebook_size = inputs.get("codebook_size", 4096)

        references = None
        raw_refs = inputs.get("references")
        if raw_refs:
            references = []
            for ref_data in raw_refs:
                vq_codes = ref_data.get("vq_codes")
                if vq_codes is not None and not isinstance(vq_codes, torch.Tensor):
                    vq_codes = torch.tensor(vq_codes)
                else:
                    pass
                if vq_codes is None and fish_reference_payload_is_supported(ref_data):
                    vq_codes = reference_encode_service.get_or_encode(
                        ref_data,
                        desc="FishAudio S2-Pro reference",
                    )
                else:
                    pass
                references.append(
                    Reference(
                        audio_bytes=b"",
                        text=ref_data.get("text", ""),
                        vq_codes=vq_codes,
                    )
                )
        else:
            pass

        prompt_data = adapter.build_prompt(
            text=text, references=references, num_codebooks=num_codebooks
        )
        state = S2ProState(
            input_ids=prompt_data["input_ids"],
            vq_mask_tokens=prompt_data["vq_mask_tokens"],
            vq_parts=prompt_data["vq_parts"],
            num_codebooks=num_codebooks,
            codebook_size=codebook_size,
            max_new_tokens=params.get("max_new_tokens", 1024),
            temperature=params.get("temperature", 0.8),
            top_p=params.get("top_p", 0.8),
            top_k=params.get("top_k", 30),
            repetition_penalty=params.get("repetition_penalty", 1.1),
            seed=params.get("seed"),
        )
        return store_state(payload, state)

    return ThreadedSimpleScheduler(_preprocess, max_concurrency=worker_count)


def create_sglang_tts_engine_executor(
    model_path: str,
    *,
    device: str | None = None,
    gpu_id: int | None = None,
    max_new_tokens: int = 2048,
    top_k: int = 30,
    ras_window: int = 16,
    server_args_overrides: Mapping[str, object] | None = None,
):
    """Returns OmniScheduler for the Fish TTS AR engine."""
    del top_k
    from sglang_omni.models.fishaudio_s2_pro.engine_builder import (
        FishS2ProEngineBuilder,
    )

    return FishS2ProEngineBuilder(
        max_new_tokens=max_new_tokens,
        ras_window=ras_window,
    ).build(
        model_path,
        device=device,
        gpu_id=gpu_id,
        server_args_overrides=server_args_overrides,
    )


def create_vocoder_executor(
    model_path: str,
    *,
    device: str | None = None,
    gpu_id: int | None = None,
    max_batch_size: int = 8,
    max_batch_wait_ms: int = 2,
    stream_stride: int = 40,
    stream_followup_stride: int = 45,
    stream_overlap_tokens: int | None = 20,
    stream_crossfade_samples: int = 512,
):
    from sglang_omni.models.fishaudio_s2_pro.streaming_vocoder import (
        S2ProVocoderScheduler,
    )
    from sglang_omni.utils.device import resolve_concrete_device

    device = str(resolve_concrete_device(device, gpu_id))
    checkpoint_dir = _resolve_checkpoint(model_path)
    codec = load_codec(checkpoint_dir, device)

    return S2ProVocoderScheduler(
        codec,
        device=device,
        stream_stride=stream_stride,
        stream_followup_stride=stream_followup_stride,
        stream_overlap_tokens=stream_overlap_tokens,
        stream_crossfade_samples=stream_crossfade_samples,
        max_batch_size=max_batch_size,
        max_batch_wait_ms=max_batch_wait_ms,
    )
