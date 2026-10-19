from __future__ import annotations

import pytest
import torch
import torch.nn.functional as F
from torch.nn.attention import SDPBackend, sdpa_kernel
from transformers import WhisperConfig

from sglang_omni.models.whisper_asr import sglang_model
from sglang_omni.models.whisper_asr.sglang_model import (
    WhisperEncoderAttention,
    whisper_encoder_attention,
)


@pytest.mark.parametrize("backend", [SDPBackend.MATH, SDPBackend.FLASH_ATTENTION])
def test_encoder_attention_fallback_has_a_stable_compiler_layout(
    backend: SDPBackend,
) -> None:
    """The math SDPA backend must match the custom operator's fake output strides."""
    torch.manual_seed(13)
    projected = torch.randn(2, 7, 24)
    query, key, value = (
        states.reshape(2, 7, 2, 4) for states in projected.chunk(3, dim=-1)
    )
    with sdpa_kernel(backend):
        actual = whisper_encoder_attention(query, key, value)
        expected = F.scaled_dot_product_attention(
            query.transpose(1, 2), key.transpose(1, 2), value.transpose(1, 2)
        ).transpose(1, 2)
        torch.testing.assert_close(actual, expected)
        assert actual.is_contiguous()
        results = torch.library.opcheck(
            whisper_encoder_attention,
            (query, key, value),
            test_utils=("test_schema", "test_faketensor", "test_aot_dispatch_dynamic"),
        )
    assert set(results.values()) == {"SUCCESS"}


def test_encoder_projection_preserves_attention_math_without_fa4(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing CUDA-only dependency must preserve the original encoder computation."""
    torch.manual_seed(19)
    monkeypatch.setattr(sglang_model, "flash_attn_func", None)
    config = WhisperConfig(d_model=8, encoder_attention_heads=2)
    attention = WhisperEncoderAttention(config)
    hidden_states = torch.randn(2, 7, 8)
    query, key, value = (
        states.reshape(2, 7, 2, 4).transpose(1, 2)
        for states in attention.qkv_proj(hidden_states).chunk(3, dim=-1)
    )
    expected = attention.out_proj(
        F.scaled_dot_product_attention(query, key, value)
        .transpose(1, 2)
        .reshape(2, 7, 8)
    )
    with torch.no_grad():
        actual = attention(hidden_states)
    torch.testing.assert_close(actual, expected)


@pytest.mark.accelerator
@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
@pytest.mark.parametrize("dtype", [torch.float16, torch.bfloat16])
def test_fa4_encoder_attention_matches_sdpa_on_cuda(
    monkeypatch: pytest.MonkeyPatch, dtype: torch.dtype
) -> None:
    """Both supported dtypes preserve attention math and allow an SDPA opt-out."""
    monkeypatch.setenv("SGLANG_OMNI_WHISPER_ENCODER_ATTENTION_BACKEND", "fa4")
    if sglang_model.flash_attn_func is None:
        pytest.skip("FA4 is unavailable")
    elif torch.cuda.get_device_capability()[0] < 9:
        pytest.skip("The FA4 path requires Hopper or newer")
    else:
        torch.manual_seed(23)
        projected = torch.randn(2, 31, 384, device="cuda", dtype=dtype)
        query, key, value = (
            states.reshape(2, 31, 2, 64) for states in projected.chunk(3, dim=-1)
        )
        with torch.no_grad():
            actual = whisper_encoder_attention(query, key, value)
            expected = F.scaled_dot_product_attention(
                query.float().transpose(1, 2),
                key.float().transpose(1, 2),
                value.float().transpose(1, 2),
            ).transpose(1, 2)
        assert actual.shape == expected.shape
        assert actual.dtype == dtype
        tolerance = 2e-3 if dtype == torch.float16 else 2e-2
        torch.testing.assert_close(
            actual.float(), expected, rtol=tolerance, atol=tolerance
        )
        monkeypatch.setenv("SGLANG_OMNI_WHISPER_ENCODER_ATTENTION_BACKEND", "sdpa")
        monkeypatch.setattr(sglang_model, "flash_attn_func", pytest.fail)
        with torch.no_grad():
            fallback = whisper_encoder_attention(query, key, value)
        torch.testing.assert_close(
            fallback.float(), expected, rtol=tolerance, atol=tolerance
        )


@pytest.mark.parametrize(
    "backend,error", [("unknown", ValueError), ("fa4", RuntimeError)]
)
def test_encoder_attention_rejects_invalid_or_unavailable_backend(
    monkeypatch: pytest.MonkeyPatch, backend: str, error: type[Exception]
) -> None:
    """Explicit backend requests cannot silently select a different implementation."""
    monkeypatch.setenv("SGLANG_OMNI_WHISPER_ENCODER_ATTENTION_BACKEND", backend)
    states = torch.randn(1, 3, 2, 64)
    with pytest.raises(error):
        whisper_encoder_attention(states, states, states)
