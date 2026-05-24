# tests/test_llm_client.py
import pytest
import os
from unittest.mock import patch, MagicMock
from src.llm_client import LLMClient, create_llm_client
from src.config import Config, LLMConfig


def test_create_claude_client():
    config = Config(
        llm=LLMConfig(provider="claude", model="claude-sonnet-4-6", api_key_env="TEST_KEY")
    )
    os.environ["TEST_KEY"] = "fake-key"
    client = create_llm_client(config)
    assert client.provider == "claude"
    assert client.model == "claude-sonnet-4-6"


def test_create_openai_client():
    config = Config(
        llm=LLMConfig(provider="openai", model="gpt-4o", api_key_env="TEST_KEY2")
    )
    os.environ["TEST_KEY2"] = "fake-key"
    client = create_llm_client(config)
    assert client.provider == "openai"
    assert client.model == "gpt-4o"


def test_llm_client_complete_claude():
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_instance = MagicMock()
        mock_anthropic.return_value = mock_instance
        mock_instance.messages.create.return_value.content = [MagicMock(text="response text")]
        mock_instance.messages.create.return_value.usage.input_tokens = 100
        mock_instance.messages.create.return_value.usage.output_tokens = 50

        client = LLMClient(provider="claude", model="claude-sonnet-4-6", api_key="key")
        result = client.complete(
            system="You are helpful.",
            prompt="Say hello",
            temperature=0.5,
            max_tokens=2000,
        )
        assert result.text == "response text"
        assert result.input_tokens == 100
        assert result.output_tokens == 50


def test_llm_client_unsupported_provider():
    with pytest.raises(ValueError, match="Unsupported provider"):
        LLMClient(provider="unknown", model="x", api_key="k")
