
import pytest
from unittest.mock import patch, MagicMock
from typing import List, Dict

from gai.api.token_counter import TokenCounter

# --------------------------
# Fixtures
# --------------------------


@pytest.fixture
def mock_get_api_huggingface_key_fixture():
    """
    Fixture to mock the get_api_huggingface_key function.
    """
    with patch('gai.api.token_counter.get_api_huggingface_key') as mock_get_key:
        yield mock_get_key


@pytest.fixture
def mock_auto_tokenizer_from_pretrained_fixture():
    """
    Fixture to mock the AutoTokenizer.from_pretrained method.
    """
    with patch('transformers.AutoTokenizer.from_pretrained') as mock_tokenizer:
        yield mock_tokenizer


@pytest.fixture
def token_counter_instance(mock_get_api_huggingface_key_fixture, mock_auto_tokenizer_from_pretrained_fixture):
    """
    Fixture to provide a fresh instance of TokenCounter for tests.
    """
    return TokenCounter(model='test-model')

# --------------------------
# Helper Functions
# --------------------------


def mock_tokenizer_encode(return_values):
    """
    Helper function to create a mock tokenizer with predefined encode return values.

    Parameters:
    - return_values: A list where each element is the return value for a subsequent call to encode.

    Returns:
    - A MagicMock object with the encode method configured.
    """
    mock = MagicMock()
    mock.encode.side_effect = return_values
    return mock

# --------------------------
# TokenCounter Tests
# --------------------------


def test_count_message_tokens(mock_get_api_huggingface_key_fixture, mock_auto_tokenizer_from_pretrained_fixture):
    """
    Test counting tokens in a single message.
    """
    # Arrange
    mock_get_api_huggingface_key_fixture.return_value = 'fake_token'
    mock_tokenizer = mock_tokenizer_encode([[1, 2, 3], [4, 5, 6]])  # Simulate 3 tokens per encode call
    mock_auto_tokenizer_from_pretrained_fixture.return_value = mock_tokenizer

    tc = TokenCounter(model='test-model')

    message = {"role": "user", "content": "Hello"}

    # Act
    num_tokens = tc.count_message_tokens(message)

    # Assert
    # tokens_per_message = 3
    # role: 3 tokens
    # content: 3 tokens
    # total = 3 + 3 + 3 = 9
    assert num_tokens == 9
    assert mock_tokenizer.encode.call_count == 2
    mock_tokenizer.encode.assert_any_call("user", add_special_tokens=False)
    mock_tokenizer.encode.assert_any_call("Hello", add_special_tokens=False)


def test_count_tokens(mock_get_api_huggingface_key_fixture, mock_auto_tokenizer_from_pretrained_fixture):
    """
    Test counting tokens in a list of messages.
    """
    # Arrange
    mock_get_api_huggingface_key_fixture.return_value = 'fake_token'
    mock_tokenizer = mock_tokenizer_encode([
        [1, 2],        # "system"
        [3, 4, 5],     # "You are a helpful assistant."
        [6, 7],        # "user"
        [8, 9, 10]     # "Can you help me count tokens?"
    ])
    mock_auto_tokenizer_from_pretrained_fixture.return_value = mock_tokenizer

    tc = TokenCounter(model='test-model')

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Can you help me count tokens?"}
    ]

    # Act
    total_tokens = tc.count_tokens(messages)

    # Assert
    # First message:
    # tokens_per_message = 3
    # role: 2 tokens
    # content: 3 tokens
    # total = 3 + 2 + 3 = 8
    # Second message:
    # tokens_per_message = 3
    # role: 2 tokens
    # content: 3 tokens
    # total = 3 + 2 + 3 = 8
    # Assistant reply format: 3
    # Total: 8 + 8 + 3 = 19
    assert total_tokens == 19
    assert mock_tokenizer.encode.call_count == 4
    mock_tokenizer.encode.assert_any_call("system", add_special_tokens=False)
    mock_tokenizer.encode.assert_any_call("You are a helpful assistant.", add_special_tokens=False)
    mock_tokenizer.encode.assert_any_call("user", add_special_tokens=False)
    mock_tokenizer.encode.assert_any_call("Can you help me count tokens?", add_special_tokens=False)


def test_adjust_max_tokens_positive(mock_get_api_huggingface_key_fixture, mock_auto_tokenizer_from_pretrained_fixture):
    """
    Test adjust_max_tokens when remaining tokens are positive.
    """
    # Arrange
    mock_get_api_huggingface_key_fixture.return_value = 'fake_token'
    mock_tokenizer = mock_tokenizer_encode([[1, 2, 3], [4, 5, 6]])  # Simulate 3 tokens per encode call
    mock_auto_tokenizer_from_pretrained_fixture.return_value = mock_tokenizer

    tc = TokenCounter(model='test-model')

    messages = [
        {"role": "user", "content": "Hello"}
    ]

    max_tokens = 20

    # Act
    remaining_tokens = tc.adjust_max_tokens(messages, max_tokens)

    # Assert
    # tokens_per_message = 3
    # role: 3 tokens
    # content: 3 tokens
    # assistant reply format: 3
    # total = 3 + 3 + 3 + 3 = 12
    # remaining = 20 - 12 = 8
    assert remaining_tokens == 8


def test_adjust_max_tokens_exceed(mock_get_api_huggingface_key_fixture, mock_auto_tokenizer_from_pretrained_fixture):
    """
    Test adjust_max_tokens when message tokens exceed max_tokens.
    """
    # Arrange
    mock_get_api_huggingface_key_fixture.return_value = 'fake_token'
    mock_tokenizer = mock_tokenizer_encode([[1, 2, 3, 4], [5, 6, 7, 8]])  # Simulate 4 tokens per encode call
    mock_auto_tokenizer_from_pretrained_fixture.return_value = mock_tokenizer

    tc = TokenCounter(model='test-model')

    messages = [
        {"role": "user", "content": "Hello"}
    ]

    max_tokens = 10

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        tc.adjust_max_tokens(messages, max_tokens)

    assert "exceed max tokens" in str(exc_info.value)


def test_count_tokens_error_handling(mock_get_api_huggingface_key_fixture, mock_auto_tokenizer_from_pretrained_fixture):
    """
    Test count_tokens method handling unexpected errors.
    """
    # Arrange
    mock_get_api_huggingface_key_fixture.return_value = 'fake_token'
    mock_tokenizer = MagicMock()
    mock_tokenizer.encode.side_effect = Exception("Unexpected error")
    mock_auto_tokenizer_from_pretrained_fixture.return_value = mock_tokenizer

    tc = TokenCounter(model='test-model')

    messages = [
        {"role": "user", "content": "Hello"}
    ]

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        tc.count_tokens(messages)

    assert "Error counting tokens: Unexpected error" in str(exc_info.value)
