# SPDX-License-Identifier: Apache-2.0
"""MOSS-TTS Delay model runner for OmniScheduler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import torch
from sglang.srt.layers.sampler import multinomial_with_seed
from sglang.srt.managers.schedule_batch import ScheduleBatch
from sglang.srt.model_executor.forward_batch_info import ForwardBatch

from sglang_omni.model_runner.base import ModelRunner
from sglang_omni.model_runner.model_worker import ModelWorker
from sglang_omni.model_runner.prefill_inputs import (
    OmniPrefillInputs,
    attach_omni_prefill_inputs,
)
from sglang_omni.models.moss_tts.request_builders import (
    _INF_DELAY,
    MossTTSSGLangRequestData,
)
from sglang_omni.models.moss_tts.sampler import DelayGraphBatch
from sglang_omni.models.moss_tts.sampling_kernels import (
    multinomial_with_seed_and_token_ids,
)
from sglang_omni.scheduling.types import (
    RequestOutput,
    SchedulerOutput,
    SchedulerRequest,
)

if TYPE_CHECKING:
    from sglang.srt.managers.scheduler import GenerationBatchResult

    from sglang_omni.models.moss_tts.sglang_model import (
        ChannelLogitsList,
        MossTTSDelaySGLangModel,
    )
    from sglang_omni.scheduling.sglang_backend.output_processor import (
        SGLangOutputProcessor,
    )
else:
    pass

_NEG_INF = float("-inf")
_INT64_MAX = torch.iinfo(torch.int64).max
_UINT64_MASK = (1 << 64) - 1
_INT64_SEED_MASK = (1 << 63) - 1


@dataclass(kw_only=True)
class MossTTSDecodeJournal:
    rows: torch.Tensor
    feedback_embeddings: torch.Tensor
    next_delay_states: list[torch.Tensor]


class MossTTSModelRunner(ModelRunner):
    """Samples MOSS-TTS text/audio channels and maintains delay-pattern state."""

    model: MossTTSDelaySGLangModel
    async_enabled: bool = False
    pending_decode_journal: MossTTSDecodeJournal | None = None

    def __init__(
        self, tp_worker: ModelWorker, output_processor: SGLangOutputProcessor
    ) -> None:
        super().__init__(tp_worker, output_processor)
        self.pending_rows: torch.Tensor | None = None
        self.pending_embeds: torch.Tensor | None = None

    def custom_prefill_forward(
        self,
        forward_batch: ForwardBatch | None,
        schedule_batch: ScheduleBatch,
        requests: list[SchedulerRequest],
    ) -> None:
        del schedule_batch
        attach_omni_prefill_inputs(
            forward_batch,
            OmniPrefillInputs(
                input_embeds=self.build_prefill_input_embeds(forward_batch, requests),
            ),
        )
        return None

    def before_decode(
        self,
        forward_batch: ForwardBatch | None,
        schedule_batch: ScheduleBatch,
        requests: list[SchedulerRequest],
        *,
        is_lookahead: bool = False,
    ) -> None:
        del is_lookahead
        del schedule_batch
        self.write_decode_input_embedding(forward_batch, requests)

    def post_prefill(
        self,
        result: GenerationBatchResult,
        forward_batch: ForwardBatch | None,
        schedule_batch: ScheduleBatch,
        requests: list[SchedulerRequest],
    ) -> None:
        if schedule_batch.is_prefill_only:
            return
        else:
            pass
        self.collect_moss_step(result, forward_batch, schedule_batch, requests)

    def post_decode(
        self,
        result: GenerationBatchResult,
        forward_batch: ForwardBatch | None,
        schedule_batch: ScheduleBatch,
        requests: list[SchedulerRequest],
    ) -> None:
        self.collect_moss_step(result, forward_batch, schedule_batch, requests)

    def lookahead_eligible(self, batch: ScheduleBatch) -> bool:
        requests = [request.omni_data for request in batch.reqs]
        return (
            self.is_non_streaming_batch(requests)
            and all(
                not request.finished() and not self.req_is_retracted(request)
                for request in batch.reqs
            )
            and self.can_use_sampling_cuda_graph(
                requests, is_audio=all(request.is_audio for request in requests)
            )
            and all(
                request.lookahead_delay_slots < int(self.model.config.n_vq) - 2
                for request in requests
            )
        )

    def post_decode_launch(
        self,
        result: GenerationBatchResult,
        forward_batch: ForwardBatch | None,
        requests: list[SchedulerRequest],
    ) -> torch.Tensor | None:
        if not requests:
            return None
        else:
            pass
        sampling_positions = [
            max(request.data.generation_steps, request.data.launched_generation_steps)
            for request in requests
        ]
        self.collect_moss_step(
            result,
            forward_batch,
            None,
            requests,
            sampling_positions=sampling_positions,
        )
        assert self.pending_rows is not None and self.pending_embeds is not None
        journal = MossTTSDecodeJournal(
            rows=self.pending_rows.detach().clone(),
            feedback_embeddings=self.pending_embeds.detach().clone(),
            next_delay_states=[request.data.delay_state for request in requests],
        )
        self.pending_rows = None
        self.pending_embeds = None
        for index, request in enumerate(requests):
            request.data.launched_generation_steps = sampling_positions[index] + 1
            request.data.launch_feedback_embedding = journal.feedback_embeddings[index]
        result.moss_delay_journal = journal
        # note (Zhuofeng-Li): resolve must not queue a host copy behind the next decode.
        host_token_ids = torch.empty_like(
            result.next_token_ids, device="cpu", pin_memory=True
        )
        host_token_ids.copy_(result.next_token_ids, non_blocking=True)
        return host_token_ids

    def post_decode_resolve(
        self,
        launch_buf: torch.Tensor | None,
        result: GenerationBatchResult,
        forward_batch: ForwardBatch | None,
        schedule_batch: ScheduleBatch,
        requests: list[SchedulerRequest],
    ) -> None:
        del forward_batch, schedule_batch
        if launch_buf is None or not requests:
            return
        else:
            pass
        result.next_token_ids = launch_buf
        self.pending_decode_journal = result.moss_delay_journal
        self.pending_rows = self.pending_decode_journal.rows
        self.pending_embeds = self.pending_decode_journal.feedback_embeddings

    def build_prefill_input_embeds(
        self,
        forward_batch: ForwardBatch,
        requests: list[SchedulerRequest],
    ) -> torch.Tensor:
        pieces = []
        for sched_req in requests:
            data: MossTTSSGLangRequestData = sched_req.data
            req = data.req
            rows = data.prompt_rows
            if rows is None:
                raise RuntimeError("MOSS-TTS prefill requires prompt_rows")
            else:
                pass
            req_len = int(req.extend_range.length)
            prefix_len = len(req.prefix_indices)
            if data.output_rows:
                # note (Richard Wang): prompt_rows is short by the generated tail
                generated = torch.stack(data.output_rows, dim=0)
                rows = torch.cat([rows.to(generated.device), generated], dim=0)
            else:
                pass
            current_rows = rows[prefix_len : prefix_len + req_len]
            if int(current_rows.shape[0]) != req_len:
                raise RuntimeError(
                    f"MOSS-TTS prefill row mismatch for {req.rid}: have "
                    f"{int(current_rows.shape[0])} rows, need {req_len} "
                    f"(prefix={prefix_len}, prompt={int(data.prompt_rows.shape[0])}, "
                    f"generated={len(data.output_rows)})"
                )
            else:
                pass
            if data.output_rows:
                # note (Richard Wang): leftover row would decode instead of new sample
                data.pending_feedback_queue.clear()
                if self.async_enabled:
                    data.launch_feedback_embedding = None
                    data.launched_generation_steps = data.generation_steps
                    data.delay_state = data.committed_delay_state
                else:
                    pass
            else:
                pass
            embeds = self.model.prepare_multi_modal_inputs(
                current_rows.to(device=forward_batch.input_ids.device)
            )
            pieces.append(embeds)
        if not pieces:
            return torch.empty(
                (0, self.model.hidden_size),
                device=forward_batch.input_ids.device,
                dtype=self.model.dtype,
            )
        else:
            pass
        return torch.cat(pieces, dim=0).to(
            device=forward_batch.input_ids.device,
            dtype=self.model.dtype,
        )

    def write_decode_input_embedding(
        self,
        forward_batch: ForwardBatch,
        requests: list[SchedulerRequest],
    ) -> None:
        batch_size = len(requests)
        if batch_size == 0:
            return
        else:
            pass
        embedding = self.model.decode_input_embedding
        weight = embedding.weight
        if forward_batch.input_ids.numel() < batch_size:
            raise RuntimeError(
                "MOSS-TTS decode input_ids must contain one row id per request"
            )
        else:
            pass
        if batch_size > int(weight.shape[0]):
            raise RuntimeError(
                "MOSS-TTS decode batch exceeds the staged decode-embedding rows "
                f"({batch_size} > {int(weight.shape[0])})"
            )
        else:
            pass
        rows = []
        for sched_req in requests:
            if (
                self.async_enabled
                and sched_req.data.launch_feedback_embedding is not None
            ):
                rows.append(sched_req.data.launch_feedback_embedding)
                sched_req.data.launch_feedback_embedding = None
                continue
            else:
                pass
            queue = sched_req.data.pending_feedback_queue
            if not queue:
                rows.append(torch.zeros(self.model.hidden_size, device=weight.device))
                continue
            else:
                pass
            if hasattr(queue, "popleft"):
                rows.append(queue.popleft())
            else:
                rows.append(queue.pop(0))
        stacked = torch.stack(rows, dim=0).to(device=weight.device, dtype=weight.dtype)
        with torch.no_grad():
            weight[:batch_size].copy_(stacked)

        row_ids = torch.arange(
            batch_size,
            dtype=torch.long,
            device=forward_batch.input_ids.device,
        )
        forward_batch.input_ids[:batch_size].copy_(row_ids)

    def collect_moss_step(
        self,
        result: GenerationBatchResult,
        forward_batch: ForwardBatch | None,
        schedule_batch: ScheduleBatch | None,
        requests: list[SchedulerRequest],
        *,
        sampling_positions: list[int] | None = None,
    ) -> None:
        datas: list[MossTTSSGLangRequestData] = [
            sched_req.data for sched_req in requests
        ]
        is_audio = bool(datas) and all(data.is_audio for data in datas)
        channel_logits = self.channel_logits_from_result(
            result,
            forward_batch,
            is_audio=is_audio,
        )
        n_vq = len(channel_logits) - 1
        if n_vq <= 0:
            raise RuntimeError("MOSS-TTS requires at least one audio codebook head")
        else:
            pass
        if not requests:
            return
        else:
            pass

        embeds: torch.Tensor | None = None
        if self.can_use_sampling_cuda_graph(datas, is_audio=is_audio):
            rows, embeds = self.sample_rows_graphed(
                channel_logits, datas, sampling_positions=sampling_positions
            )
        else:
            assert sampling_positions is None, "MOSS lookahead requires sampling graphs"
            rows = self.sample_rows(
                channel_logits,
                datas,
                n_vq=n_vq,
                is_audio=is_audio,
            )

        next_token_ids = rows[:, 0].contiguous()
        result.next_token_ids = next_token_ids
        if embeds is None:
            embeds = self.model.prepare_multi_modal_inputs(
                rows.to(device=self.model.device)
            )
        else:
            pass
        self.pending_rows = rows
        self.pending_embeds = embeds.detach()
        self.pending_decode_journal = None

    def can_use_sampling_cuda_graph(
        self,
        datas: list[MossTTSSGLangRequestData],
        *,
        is_audio: bool,
    ) -> bool:
        if not is_audio or not datas:
            return False
        else:
            pass
        is_compatible = getattr(
            self.model,
            "is_sampling_cuda_graph_compatible",
            None,
        )
        if not callable(is_compatible):
            return False
        else:
            pass
        return all(
            is_compatible(data) for data in datas
        ) and self.sampling_graph_available(len(datas))

    def sampling_graph_available(self, batch_size: int) -> bool:
        available = getattr(self.model, "sampling_graph_available", None)
        return bool(callable(available) and available(batch_size))

    @staticmethod
    def is_non_streaming_batch(requests: list[MossTTSSGLangRequestData]) -> bool:
        return all(
            (payload := getattr(request, "stage_payload", None)) is not None
            and not bool(payload.request.params.get("stream", False))
            for request in requests
        )

    @staticmethod
    def sampling_metadata_tensors(
        requests: list[MossTTSSGLangRequestData],
        device: torch.device,
        *,
        generation_steps: list[int] | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if generation_steps is None:
            generation_steps = [int(request.generation_steps) for request in requests]
        else:
            pass
        if device.type == "cuda" and MossTTSModelRunner.is_non_streaming_batch(
            requests
        ):
            metadata = torch.tensor(
                [
                    [int(request.sampling_seed) for request in requests],
                    generation_steps,
                ],
                dtype=torch.long,
                device="cpu",
                pin_memory=True,
            ).to(device=device, non_blocking=True)
            return metadata[0], metadata[1]
        else:
            # note (Zhuofeng-Li): Streaming interleaves vocoder work on the same GPU.
            seeds = torch.tensor(
                [int(request.sampling_seed) for request in requests],
                dtype=torch.long,
                device=device,
            )
            generation_steps_tensor = torch.tensor(
                generation_steps,
                dtype=torch.long,
                device=device,
            )
            return seeds, generation_steps_tensor

    def sample_rows_graphed(
        self,
        channel_logits: list[torch.Tensor],
        datas: list[MossTTSSGLangRequestData],
        *,
        sampling_positions: list[int] | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        device = channel_logits[0].device
        batch_size = len(datas)
        n_vq = len(channel_logits) - 1
        delay_state = torch.stack(
            [self.delay_state_tensor(data, device) for data in datas], dim=0
        )
        seeds, generation_steps = self.sampling_metadata_tensors(
            datas, device, generation_steps=sampling_positions
        )
        audio_logits = getattr(channel_logits, "fused_audio", None)
        if audio_logits is None:
            audio_logits = torch.stack(
                [logits.to(torch.float32) for logits in channel_logits[1:]], dim=1
            )
        else:
            pass
        if tuple(audio_logits.shape[:2]) != (batch_size, n_vq):
            raise RuntimeError(
                "MOSS-TTS Delay sampling graph audio-logits shape mismatch: "
                f"got {tuple(audio_logits.shape)}"
            )
        else:
            pass
        sampling_batch = DelayGraphBatch(
            delay_state=delay_state,
            seeds=seeds,
            generation_steps=generation_steps,
        )
        if self.is_non_streaming_batch(datas):
            sampled = self.model.sample_delay_graphed(
                channel_logits[0].to(torch.float32),
                audio_logits,
                sampling_batch,
                include_feedback=True,
            )
            # note (Zhuofeng-Li): The launch journal or postprocessor owns the next copy.
            feedback_embeddings = sampled.feedback_embeddings
        else:
            sampled = self.model.sample_delay_graphed(
                channel_logits[0].to(torch.float32),
                audio_logits,
                sampling_batch,
            )
            feedback_embeddings = None
        rows = sampled.rows[:batch_size].clone()
        next_state = sampled.next_delay_state[:batch_size].clone()
        for index, data in enumerate(datas):
            data.delay_state = next_state[index]
        return rows, feedback_embeddings

    def channel_logits_from_result(
        self,
        result: GenerationBatchResult,
        forward_batch: ForwardBatch | None,
        *,
        is_audio: bool = False,
    ) -> "list[torch.Tensor] | ChannelLogitsList":
        logits_output = result.logits_output
        customized = logits_output.customized_info
        if isinstance(customized, dict):
            values = customized.get("moss_tts_channel_logits")
            if isinstance(values, list) and values:
                if is_audio:
                    token_ids = self.model.text_control_token_ids.to(
                        device=values[0].device
                    )
                    return [values[0].index_select(-1, token_ids), *values[1:]]
                else:
                    pass
                return values
            else:
                pass
        else:
            pass
        hidden_states = logits_output.hidden_states
        if isinstance(hidden_states, torch.Tensor):
            if hidden_states.ndim == 3:
                hidden_states = hidden_states[:, -1, :]
            else:
                pass
            if is_audio:
                return self.model.compute_channel_logits(
                    hidden_states,
                    forward_batch,
                    is_audio=True,
                )
            else:
                pass
            return self.model.compute_channel_logits(hidden_states, forward_batch)
        else:
            pass
        raise RuntimeError("MOSS-TTS model output did not include channel logits")

    @staticmethod
    def delay_state_tensor(
        data: MossTTSSGLangRequestData, device: torch.device
    ) -> torch.Tensor:
        state = getattr(data, "delay_state", None)
        if isinstance(state, torch.Tensor) and tuple(state.shape) == (3,):
            state = state.to(device=device, dtype=torch.long)
        else:
            delayed = (
                _INT64_MAX
                if int(getattr(data, "delayed_length", _INF_DELAY)) == _INF_DELAY
                else int(data.delayed_length)
            )
            state = torch.tensor(
                [
                    int(getattr(data, "audio_length", 0)),
                    delayed,
                    int(data.is_audio),
                ],
                dtype=torch.long,
                device=device,
            )
        data.delay_state = state
        return state

    def sample_rows(
        self,
        channel_logits: list[torch.Tensor],
        datas: list[MossTTSSGLangRequestData],
        *,
        n_vq: int,
        is_audio: bool = False,
    ) -> torch.Tensor:
        """One batched MOSS-TTS delay-pattern decode step over the whole batch.

        A vectorized port of one ``MossTTSDelayModel.generate`` step; per-request
        delay state is gathered from the ``data`` objects and scattered back.
        """
        cfg = self.model.config
        device = channel_logits[0].device
        batch_size = len(datas)

        pad_token_id = int(cfg.pad_token_id)
        gen_slot = int(cfg.audio_assistant_gen_slot_token_id)
        delay_slot = int(cfg.audio_assistant_delay_slot_token_id)
        audio_start = int(cfg.audio_start_token_id)
        audio_end = int(cfg.audio_end_token_id)
        im_end = int(cfg.im_end_token_id)
        audio_pad_code = int(cfg.audio_pad_code)

        delay_state = torch.stack(
            [self.delay_state_tensor(d, device) for d in datas], dim=0
        )
        audio_lengths = delay_state[:, 0]
        delayed = delay_state[:, 1]
        audio_mask = delay_state[:, 2].bool()
        sampling_seeds, gen_steps = self.sampling_metadata_tensors(datas, device)
        text_temp = torch.tensor(
            [float(d.text_temperature) for d in datas],
            dtype=torch.float32,
            device=device,
        )
        audio_temp = torch.tensor(
            [float(d.audio_temperature) for d in datas],
            dtype=torch.float32,
            device=device,
        )
        text_top_p = torch.tensor(
            [float(d.text_top_p) for d in datas], dtype=torch.float32, device=device
        )
        text_top_k = torch.tensor(
            [int(d.text_top_k) for d in datas], dtype=torch.long, device=device
        )
        audio_top_p = torch.tensor(
            [float(d.audio_top_p) for d in datas], dtype=torch.float32, device=device
        )
        audio_top_k = torch.tensor(
            [int(d.audio_top_k) for d in datas], dtype=torch.long, device=device
        )
        audio_rep = torch.tensor(
            [float(d.audio_repetition_penalty) for d in datas],
            dtype=torch.float32,
            device=device,
        )
        num_channels = n_vq + 1

        text_logits = channel_logits[0].to(torch.float32)
        next_text = torch.full(
            (batch_size,), pad_token_id, dtype=torch.long, device=device
        )
        next_text[delayed < n_vq] = delay_slot
        is_audio_eos = delayed == n_vq
        next_text[is_audio_eos] = audio_end
        audio_mask = audio_mask & ~is_audio_eos
        text_candidate_token_ids: torch.Tensor | None = None
        if is_audio:
            if int(text_logits.shape[-1]) != 2:
                raise RuntimeError(
                    "MOSS-TTS control-only text logits must have two columns"
                )
            else:
                pass
            text_candidate_token_ids = self.model.text_control_token_ids.to(
                device=device
            )
            sampling_text_mask = audio_mask & (delayed > n_vq)
            step0 = gen_steps == 0
            if bool(step0.any()):
                text_logits[step0, 1] = _NEG_INF
            else:
                pass
        else:
            vocab = text_logits.shape[-1]
            sampling_text_mask = delayed > n_vq
            not_audio = ~audio_mask
            if bool(not_audio.any()):
                exclude = torch.tensor(
                    [
                        t
                        for t in (pad_token_id, gen_slot, delay_slot, audio_end)
                        if 0 <= t < vocab
                    ],
                    dtype=torch.long,
                    device=device,
                )
                text_logits[not_audio] = text_logits[not_audio].index_fill(
                    -1, exclude, _NEG_INF
                )
            else:
                pass
            if bool(audio_mask.any()):
                allow_only = torch.ones(vocab, dtype=torch.bool, device=device)
                for token_id in (gen_slot, delay_slot):
                    if 0 <= token_id < vocab:
                        allow_only[token_id] = False
                    else:
                        pass
                text_logits[audio_mask] = text_logits[audio_mask].masked_fill(
                    allow_only, _NEG_INF
                )
            else:
                pass

            if 0 <= delay_slot < vocab:
                step0 = gen_steps == 0
                if bool(step0.any()):
                    text_logits[step0, delay_slot] = _NEG_INF
                else:
                    pass
            else:
                pass
            if 0 <= im_end < vocab:
                step_le_nvq = gen_steps <= n_vq
                if bool(step_le_nvq.any()):
                    text_logits[step_le_nvq, im_end] = _NEG_INF
                else:
                    pass
            else:
                pass

        if bool(sampling_text_mask.any()):
            idx = sampling_text_mask.nonzero(as_tuple=False).squeeze(1)
            next_text[idx] = self.sample_tokens(
                text_logits[idx],
                temperature=text_temp[idx],
                top_p=text_top_p[idx],
                top_k=text_top_k[idx],
                seeds=sampling_seeds[idx],
                positions=gen_steps[idx] * num_channels,
                candidate_token_ids=text_candidate_token_ids,
            )
        else:
            pass
        audio_mask = audio_mask | (next_text == audio_start)
        audio_mask = audio_mask & (next_text != im_end)

        next_audio = torch.full(
            (batch_size, n_vq), audio_pad_code, dtype=torch.long, device=device
        )
        channel_idx = torch.arange(n_vq, device=device)
        pre_audio = audio_lengths.unsqueeze(1) > channel_idx.unsqueeze(0)
        post_audio = channel_idx.unsqueeze(0) > (delayed.unsqueeze(1) - 1)
        post_audio = post_audio | (delayed == _INT64_MAX).unsqueeze(1)
        sampling_audio_mask = pre_audio & post_audio
        if bool(sampling_audio_mask.any()):
            audio_logits = getattr(channel_logits, "fused_audio", None)
            if audio_logits is None:
                audio_logits = torch.stack(
                    [cl.to(torch.float32) for cl in channel_logits[1:]], dim=1
                )  # [batch, n_vq, vocab_audio]
            else:
                pass
            if 0 <= audio_pad_code < audio_logits.shape[-1]:
                audio_logits[..., audio_pad_code:] = _NEG_INF
            else:
                pass
            if bool((audio_rep != 1.0).any()):
                self.apply_audio_repetition_penalty(audio_logits, datas, n_vq=n_vq)
            else:
                pass
            audio_temp_full = audio_temp.unsqueeze(1).expand(batch_size, n_vq)
            audio_top_p_full = audio_top_p.unsqueeze(1).expand(batch_size, n_vq)
            audio_top_k_full = audio_top_k.unsqueeze(1).expand(batch_size, n_vq)
            mask_idx = sampling_audio_mask.nonzero(as_tuple=False)
            audio_rows = mask_idx[:, 0]
            audio_chans = mask_idx[:, 1]
            next_audio[sampling_audio_mask] = self.sample_tokens(
                audio_logits[sampling_audio_mask],
                temperature=audio_temp_full[sampling_audio_mask],
                top_p=audio_top_p_full[sampling_audio_mask],
                top_k=audio_top_k_full[sampling_audio_mask],
                seeds=sampling_seeds[audio_rows],
                positions=gen_steps[audio_rows] * num_channels + (audio_chans + 1),
            )
        else:
            pass

        increment = (
            (next_text == audio_start)
            | (next_text == gen_slot)
            | (next_text == delay_slot)
        )
        audio_lengths = audio_lengths + increment.long()
        audio_lengths[next_text == audio_end] = 0
        delayed[(delayed == _INT64_MAX) & (next_text == delay_slot)] = 0
        not_inf = delayed != _INT64_MAX
        delayed[not_inf] = delayed[not_inf] + 1
        delayed[delayed > n_vq] = _INT64_MAX

        next_state = torch.stack((audio_lengths, delayed, audio_mask.long()), dim=1)
        for i, data in enumerate(datas):
            data.delay_state = next_state[i].detach()
            if device.type == "cpu":
                data.audio_length = int(next_state[i, 0])
                delayed_i = int(next_state[i, 1])
                data.delayed_length = (
                    _INF_DELAY if delayed_i == _INT64_MAX else delayed_i
                )
                data.is_audio = bool(int(next_state[i, 2]))
            else:
                pass

        rows = torch.empty((batch_size, n_vq + 1), dtype=torch.long, device=device)
        rows[:, 0] = next_text
        rows[:, 1:] = next_audio
        return rows

    @staticmethod
    def as_row_tensor(
        value: torch.Tensor | float | int,
        num_rows: int,
        dtype: torch.dtype,
        device: torch.device,
    ) -> torch.Tensor:
        """Broadcast a scalar to a per-row tensor, or move an existing one."""
        if isinstance(value, torch.Tensor):
            return value.to(dtype=dtype, device=device)
        else:
            pass
        return torch.full((num_rows,), value, dtype=dtype, device=device)

    @staticmethod
    def sample_tokens(
        logits: torch.Tensor,
        *,
        temperature: torch.Tensor | float,
        top_p: torch.Tensor | float,
        top_k: torch.Tensor | int,
        seeds: torch.Tensor,
        positions: torch.Tensor,
        candidate_token_ids: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Per-row temperature / top-k / top-p sampling for ``[N, vocab]`` logits.

        ``temperature``/``top_p``/``top_k`` may be scalars or per-row tensors of
        length N and are applied entirely through vectorized tensor masks (no
        ``.tolist()`` or Python-side grouping, so each row keeps its own params).
        When ``candidate_token_ids`` is provided, ``logits`` must contain exactly
        those two candidates; sampling hashes their original vocabulary ids and
        maps the local sampled column back to the original id. Rows with
        temperature <= 0, or rows left fully masked, fall back to greedy argmax;
        ``logits`` is float32 with disallowed tokens already masked to ``-inf``.
        """
        num_rows = int(logits.shape[0])
        if num_rows == 0:
            return torch.empty(0, dtype=torch.long, device=logits.device)
        else:
            pass
        device = logits.device
        if candidate_token_ids is not None:
            candidate_token_ids = candidate_token_ids.to(device=device)
            if tuple(logits.shape[1:]) != (2,) or int(candidate_token_ids.numel()) != 2:
                raise ValueError(
                    "MOSS-TTS compact candidate sampling requires exactly two tokens"
                )
            else:
                pass
        else:
            pass

        temp = MossTTSModelRunner.as_row_tensor(
            temperature, num_rows, torch.float32, device
        )
        top_p_row = MossTTSModelRunner.as_row_tensor(
            top_p, num_rows, torch.float32, device
        )
        top_k_row = MossTTSModelRunner.as_row_tensor(
            top_k, num_rows, torch.long, device
        )
        do_sample = temp > 0
        safe_temp = torch.where(do_sample, temp, torch.ones_like(temp))
        scores = logits / safe_temp.unsqueeze(1)
        if candidate_token_ids is not None:
            scores = MossTTSModelRunner.apply_two_token_top_k(scores, top_k_row)
            scores = MossTTSModelRunner.apply_top_p(
                scores,
                top_p_row,
                skip_inactive_check=True,
            )
        else:
            scores = MossTTSModelRunner.apply_top_k(scores, top_k_row)
            scores = MossTTSModelRunner.apply_top_p(scores, top_p_row)

        probs = torch.softmax(scores, dim=-1)
        probs = torch.nan_to_num(probs, nan=0.0, posinf=0.0, neginf=0.0)

        seeds_row = MossTTSModelRunner.as_row_tensor(
            seeds, num_rows, torch.long, device
        )
        positions_row = MossTTSModelRunner.as_row_tensor(
            positions, num_rows, torch.long, device
        )
        fallback = (~do_sample) | (probs.sum(dim=-1) <= 0)
        sampled = torch.argmax(logits, dim=-1)
        if candidate_token_ids is not None:
            if device.type == "cpu":
                candidate_sampled = MossTTSModelRunner.multinomial_with_seed_cpu(
                    probs,
                    seeds_row,
                    positions_row,
                )
            else:
                candidate_sampled = multinomial_with_seed_and_token_ids(
                    scores,
                    seeds_row,
                    positions_row,
                    candidate_token_ids,
                )
            sampled = torch.where(fallback, sampled, candidate_sampled)
            return candidate_token_ids[sampled].to(torch.long)
        else:
            pass

        sample_mask = ~fallback
        if bool(sample_mask.any()):
            if device.type == "cpu":
                sampled[sample_mask] = MossTTSModelRunner.multinomial_with_seed_cpu(
                    probs[sample_mask],
                    seeds_row[sample_mask],
                    positions_row[sample_mask],
                )
            else:
                # Note:(Chenchen Hong) post1's multinomial_with_seed is Gumbel-max
                # and wants logits, not probs (probs lost the -inf masking and made
                # MOSS emit only the pad code); the CPU fallback still needs probs.
                sampled[sample_mask] = multinomial_with_seed(
                    scores[sample_mask],
                    seeds_row[sample_mask],
                    positions_row[sample_mask],
                ).view(-1)
        else:
            pass
        return sampled.to(torch.long)

    @staticmethod
    def apply_two_token_top_k(
        scores: torch.Tensor,
        top_k_row: torch.Tensor,
    ) -> torch.Tensor:
        """Apply the only active compact top-k case without a host sync."""
        top1 = top_k_row == 1
        top1_threshold = scores.max(dim=-1, keepdim=True).values
        return scores.masked_fill(
            top1.unsqueeze(1) & (scores < top1_threshold), _NEG_INF
        )

    @staticmethod
    def multinomial_with_seed_cpu(
        probs: torch.Tensor,
        seeds: torch.Tensor,
        positions: torch.Tensor,
    ) -> torch.Tensor:
        """CPU-only seeded fallback; approximates the GPU sampler (not bit-exact)."""
        sampled = torch.empty(probs.shape[0], dtype=torch.long, device=probs.device)
        for row_idx in range(probs.shape[0]):
            row = probs[row_idx]
            if float(row.sum().item()) <= 0.0:
                sampled[row_idx] = 0
                continue
            else:
                pass
            seed = int(seeds[row_idx].item()) & _UINT64_MASK
            position = int(positions[row_idx].item()) & _UINT64_MASK
            mixed_seed = (
                seed
                ^ ((position + 0x9E3779B97F4A7C15) & _UINT64_MASK)
                ^ ((position << 17) & _UINT64_MASK)
            ) & _INT64_SEED_MASK
            generator = torch.Generator(device="cpu")
            generator.manual_seed(mixed_seed)
            sampled[row_idx] = torch.multinomial(
                row.cpu(), num_samples=1, generator=generator
            ).to(device=probs.device)
        return sampled

    @staticmethod
    def apply_top_k(scores: torch.Tensor, top_k_row: torch.Tensor) -> torch.Tensor:
        """Per-row top-k mask; rows with k <= 0 or k >= vocab are left untouched."""
        vocab = scores.shape[-1]
        active = (top_k_row > 0) & (top_k_row < vocab)
        if not bool(active.any()):
            return scores
        else:
            pass
        k_clamped = top_k_row.clamp(min=1, max=vocab)
        max_top_k = int(k_clamped[active].max().item())
        topk_scores, _ = torch.topk(scores, k=max_top_k, dim=-1)
        gather_k = torch.where(active, k_clamped, torch.ones_like(k_clamped))
        gather_k = gather_k.clamp(min=1, max=max_top_k)
        kth = topk_scores.gather(1, (gather_k - 1).unsqueeze(1))
        threshold = torch.where(
            active.unsqueeze(1), kth, torch.full_like(kth, _NEG_INF)
        )
        return scores.masked_fill(scores < threshold, _NEG_INF)

    @staticmethod
    def apply_top_p(
        scores: torch.Tensor,
        top_p_row: torch.Tensor,
        *,
        skip_inactive_check: bool = False,
    ) -> torch.Tensor:
        """Apply per-row nucleus masking.

        ``skip_inactive_check`` keeps the compact hot path tensor-only instead
        of synchronizing with the host just to discover that every row uses
        ``top_p=1``.
        """
        active = (top_p_row > 0.0) & (top_p_row < 1.0)
        if not skip_inactive_check and not bool(active.any()):
            return scores
        else:
            pass
        # Note (Jiaxin Deng): input order on ties is the one contract the graphed,
        # branchless and eager paths share; an unstable sort breaks it per backend.
        sorted_scores, sorted_indices = torch.sort(
            scores, descending=True, dim=-1, stable=True
        )
        probs = torch.softmax(sorted_scores, dim=-1)
        cumulative = torch.cumsum(probs, dim=-1)
        remove = cumulative > top_p_row.unsqueeze(1)
        remove[..., 1:] = remove[..., :-1].clone()
        remove[..., 0] = False
        remove = remove & active.unsqueeze(1)
        remove_scattered = torch.zeros_like(scores, dtype=torch.bool).scatter_(
            -1, sorted_indices, remove
        )
        return scores.masked_fill(remove_scattered, _NEG_INF)

    @staticmethod
    def apply_audio_repetition_penalty(
        audio_logits: torch.Tensor,
        datas: list[MossTTSSGLangRequestData],
        *,
        n_vq: int,
    ) -> None:
        """In-place delay-pattern repetition penalty, per request and codebook.

        Each request's own ``audio_repetition_penalty`` is applied (requests with
        a unit penalty are skipped). Only invoked when at least one request has a
        non-unit penalty (off by default), so this per-request loop is off the
        hot path.
        """
        device = audio_logits.device
        vocab = audio_logits.shape[-1]
        for i, data in enumerate(datas):
            penalty = float(data.audio_repetition_penalty)
            if penalty == 1.0:
                continue
            else:
                pass
            parts = []
            prompt_rows = getattr(data, "prompt_rows", None)
            if prompt_rows is not None and prompt_rows.numel() > 0:
                parts.append(prompt_rows[:, 1:])
            else:
                pass
            output_rows = getattr(data, "output_rows", None)
            if output_rows:
                parts.append(torch.stack(output_rows, dim=0)[:, 1:])
            else:
                pass
            if not parts:
                continue
            else:
                pass
            history = torch.cat(
                [part.to(device=device, dtype=torch.long) for part in parts], dim=0
            )
            for channel in range(n_vq):
                tokens = torch.unique(history[:, channel])
                tokens = tokens[(tokens >= 0) & (tokens < vocab)]
                if tokens.numel() == 0:
                    continue
                else:
                    pass
                scores = audio_logits[i, channel, tokens]
                audio_logits[i, channel, tokens] = torch.where(
                    scores > 0, scores / penalty, scores * penalty
                )

    def post_process_outputs(
        self,
        result: GenerationBatchResult,
        scheduler_output: SchedulerOutput,
        outputs: dict[str, RequestOutput],
    ) -> None:
        del result
        rows = self.pending_rows
        embeds = self.pending_embeds
        journal = self.pending_decode_journal
        self.pending_rows = None
        self.pending_embeds = None
        self.pending_decode_journal = None
        if rows is None or embeds is None:
            return
        else:
            pass

        can_copy_batch = self.is_non_streaming_batch(
            [request.data for request in scheduler_output.requests]
        )
        if can_copy_batch and journal is None:
            rows = rows.detach().clone()
            embeds = embeds.detach().clone()
        else:
            pass
        eos_id = int(self.model.config.im_end_token_id)
        audio_start_id = int(self.model.config.audio_start_token_id)
        audio_end_id = int(self.model.config.audio_end_token_id)
        for row_idx, sched_req in enumerate(scheduler_output.requests):
            if journal is not None:
                request = sched_req.data.req
                assert request is not None
                if request.finished() or self.req_is_retracted(request):
                    sched_req.data.delay_state = sched_req.data.committed_delay_state
                    sched_req.data.launched_generation_steps = (
                        sched_req.data.generation_steps
                    )
                    sched_req.data.launch_feedback_embedding = None
                    continue
                else:
                    pass
            else:
                pass
            req_output = outputs[sched_req.request_id]
            if req_output.data is None:
                continue
            else:
                pass
            text_token_id = int(req_output.data)
            if self.async_enabled:
                sched_req.data.committed_delay_state = (
                    journal.next_delay_states[row_idx]
                    if journal is not None
                    else sched_req.data.delay_state
                )
                if text_token_id == int(
                    self.model.config.audio_assistant_delay_slot_token_id
                ):
                    sched_req.data.lookahead_delay_slots += 1
                elif text_token_id in (audio_start_id, audio_end_id):
                    sched_req.data.lookahead_delay_slots = 0
                else:
                    pass
            else:
                pass
            if text_token_id == audio_start_id:
                sched_req.data.is_audio = True
            elif text_token_id == audio_end_id:
                sched_req.data.is_audio = False
            else:
                pass
            if text_token_id == eos_id:
                continue
            else:
                pass
            output_row = rows[row_idx]
            feedback_embedding = embeds[row_idx]
            if can_copy_batch:
                pass
            else:
                output_row = output_row.detach().clone()
                feedback_embedding = feedback_embedding.detach().clone()
            sched_req.data.output_rows.append(output_row)
            if journal is None:
                sched_req.data.pending_feedback_queue.append(feedback_embedding)
            else:
                pass
