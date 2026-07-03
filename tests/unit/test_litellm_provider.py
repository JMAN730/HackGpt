"""Unit tests for the LiteLLM AI gateway provider."""

import sys
import types
import pytest
from unittest import mock

from ai_engine.model_registry import ModelProvider, MODEL_CATALOG
from ai_engine.providers import LiteLLMProvider, ProviderFactory


def test_litellm_in_model_provider_enum():
    """LiteLLM must be a member of the ModelProvider enum."""
    assert hasattr(ModelProvider, "LITELLM")
    assert ModelProvider.LITELLM.value == "litellm"


def test_litellm_catalog_entries():
    """Verify representative LiteLLM catalog entries exist."""
    assert "litellm/anthropic/claude-sonnet-4-20250514" in MODEL_CATALOG
    assert "litellm/gpt-4o" in MODEL_CATALOG
    assert "litellm/gemini/gemini-2.5-flash" in MODEL_CATALOG

    entry = MODEL_CATALOG["litellm/gpt-4o"]
    assert entry.provider == ModelProvider.LITELLM
    assert entry.model_id == "gpt-4o"


def test_provider_factory_resolves_litellm(monkeypatch):
    """ProviderFactory should return a LiteLLMProvider for LiteLLM models."""
    monkeypatch.setenv("LITELLM_API_KEY", "test-key")
    ProviderFactory._providers.pop(ModelProvider.LITELLM, None)

    provider, info = ProviderFactory.get_provider_for_model("litellm/gpt-4o")
    assert provider.provider_name == "LiteLLM"
    assert info.model_id == "gpt-4o"


def test_is_available_with_litellm_key(monkeypatch):
    """Available when LITELLM_API_KEY is set."""
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_API_KEY", raising=False)

    prov = LiteLLMProvider()
    assert prov.is_available() is False

    monkeypatch.setenv("LITELLM_API_KEY", "sk-test")
    prov_with_key = LiteLLMProvider()
    assert prov_with_key.is_available() is True


def test_is_available_with_provider_key(monkeypatch):
    """Available when a provider-specific key (e.g. OPENAI_API_KEY) is set."""
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_API_KEY", raising=False)

    prov = LiteLLMProvider()
    assert prov.is_available() is False

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    prov2 = LiteLLMProvider()
    assert prov2.is_available() is True


def test_chat_completion_calls_litellm(monkeypatch):
    """chat_completion should delegate to litellm.completion with drop_params=True."""
    fake_litellm = types.ModuleType("litellm")

    mock_choice = mock.MagicMock()
    mock_choice.message.content = "Test response from LiteLLM"
    mock_response = mock.MagicMock()
    mock_response.choices = [mock_choice]
    fake_litellm.completion = mock.MagicMock(return_value=mock_response)

    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    prov = LiteLLMProvider(api_key="sk-test")
    result = prov.chat_completion(
        model_id="anthropic/claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=100,
        temperature=0.5,
    )

    assert result == "Test response from LiteLLM"
    fake_litellm.completion.assert_called_once()

    call_kwargs = fake_litellm.completion.call_args[1]
    assert call_kwargs["model"] == "anthropic/claude-sonnet-4-20250514"
    assert call_kwargs["drop_params"] is True
    assert call_kwargs["api_key"] == "sk-test"
    assert call_kwargs["temperature"] == 0.5
    assert call_kwargs["max_tokens"] == 100


def test_chat_completion_omits_key_when_empty(monkeypatch):
    """api_key should be omitted from kwargs when not set."""
    fake_litellm = types.ModuleType("litellm")

    mock_choice = mock.MagicMock()
    mock_choice.message.content = "response"
    mock_response = mock.MagicMock()
    mock_response.choices = [mock_choice]
    fake_litellm.completion = mock.MagicMock(return_value=mock_response)

    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)

    prov = LiteLLMProvider()
    prov.chat_completion(
        model_id="gpt-4o",
        messages=[{"role": "user", "content": "Hi"}],
    )

    call_kwargs = fake_litellm.completion.call_args[1]
    assert "api_key" not in call_kwargs


def test_chat_completion_passes_base_url(monkeypatch):
    """api_base should be forwarded when base_url is set."""
    fake_litellm = types.ModuleType("litellm")

    mock_choice = mock.MagicMock()
    mock_choice.message.content = "response"
    mock_response = mock.MagicMock()
    mock_response.choices = [mock_choice]
    fake_litellm.completion = mock.MagicMock(return_value=mock_response)

    monkeypatch.setitem(sys.modules, "litellm", fake_litellm)

    prov = LiteLLMProvider(api_key="key", base_url="http://localhost:4000")
    prov.chat_completion(
        model_id="gpt-4o",
        messages=[{"role": "user", "content": "Hi"}],
    )

    call_kwargs = fake_litellm.completion.call_args[1]
    assert call_kwargs["api_base"] == "http://localhost:4000"


def test_import_error_when_litellm_missing(monkeypatch):
    """Should raise ImportError with install instructions when litellm is absent."""
    monkeypatch.setitem(sys.modules, "litellm", None)

    prov = LiteLLMProvider(api_key="key")
    with pytest.raises(ImportError, match="pip install litellm"):
        prov.chat_completion(
            model_id="gpt-4o",
            messages=[{"role": "user", "content": "Hi"}],
        )
