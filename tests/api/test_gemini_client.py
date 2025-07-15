import sys
import types
import os
from unittest.mock import Mock, patch
import pytest

from gai_tool.api.gemini_client import GeminiClient


@pytest.fixture
def mock_env_api_key():
    """Provide a fake GEMINI_API_KEY in the environment for the duration of a test."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake-gemini-key"}):
        yield


@pytest.fixture
def mock_chat_google_generative_ai():
    """Patch ``ChatGoogleGenerativeAI`` to avoid real network calls."""
    with patch("gai_tool.api.gemini_client.ChatGoogleGenerativeAI") as mock_chat:
        mock_instance = Mock()
        mock_chat.return_value = mock_instance
        yield mock_chat, mock_instance


@pytest.fixture
def mock_validate_messages():
    """Patch ``validate_messages`` so we can assert it was called without executing its logic."""
    with patch("gai_tool.api.gemini_client.validate_messages", return_value=True) as mock_validate:
        yield mock_validate


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_initialization_success(mock_env_api_key, mock_chat_google_generative_ai):
    """GeminiClient should initialize correctly when an API key is present."""
    mock_chat, _ = mock_chat_google_generative_ai

    client = GeminiClient()

    # Assert the underlying LLM class was instantiated with expected defaults
    mock_chat.assert_called_once_with(
        model="gemini-pro",
        google_api_key="fake-gemini-key",
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        max_output_tokens=8000,
        callback_manager=None,
    )
    # The created instance should be assigned to the client
    assert client.llm is mock_chat.return_value


def test_initialization_missing_api_key():
    """GeminiClient should raise an error if no API key is provided via env vars."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="Gemini API key must be provided"):
            GeminiClient()


def test_get_chat_completion_success(mock_env_api_key, mock_chat_google_generative_ai, mock_validate_messages):
    """get_chat_completion should validate messages, forward the call and return the content."""
    _, mock_llm = mock_chat_google_generative_ai

    # Arrange the LLM's invoke return value
    mock_llm.invoke.return_value = Mock(content="hello world")

    messages = [{"role": "user", "content": "Say hi"}]

    client = GeminiClient()
    result = client.get_chat_completion(user_message=messages)

    # Assert
    mock_validate_messages.assert_called_once_with(messages=messages)
    mock_llm.invoke.assert_called_once_with(messages)
    assert result == "hello world"


def test_get_chat_completion_error(mock_env_api_key, mock_chat_google_generative_ai, mock_validate_messages):
    """If the underlying LLM raises an exception, GeminiClient should wrap and propagate it."""
    _, mock_llm = mock_chat_google_generative_ai

    mock_llm.invoke.side_effect = Exception("network failure")

    client = GeminiClient()
    messages = [{"role": "user", "content": "something"}]

    with pytest.raises(Exception, match="Error while communicating with Gemini: network failure"):
        client.get_chat_completion(user_message=messages)

    mock_validate_messages.assert_called_once_with(messages=messages)
    mock_llm.invoke.assert_called_once_with(messages)
