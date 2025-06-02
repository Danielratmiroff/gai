from gai_tool.src.utils import get_api_huggingface_key
from tokenizers import Tokenizer
from huggingface_hub import hf_hub_download
from typing import List, Dict, Optional
import logging
import os

# Set logging level to reduce noise
logging.getLogger("tokenizers").setLevel(logging.ERROR)


class TokenCounterLite:
    """
    Lightweight token counter using the standalone tokenizers library.
    This avoids the PyTorch/TensorFlow warning from transformers.
    """

    def __init__(self, model: str):
        """
        Initialize token counter with specified model using tokenizers library.

        Parameters:
        - model: The name or path of the model.
        """
        self.tokens_per_message = 3  # Every message follows {role/name, content}
        self.model = model
        self.tokenizer = self._load_tokenizer()

    def _load_tokenizer(self) -> Tokenizer:
        """Load tokenizer from HuggingFace Hub."""
        try:
            # Attempt to load token from environment variable
            hf_token = get_api_huggingface_key()

            # Download tokenizer.json file
            tokenizer_path = hf_hub_download(
                repo_id=self.model,
                filename="tokenizer.json",
                token=hf_token if hf_token else None
            )

            # Load tokenizer from file
            return Tokenizer.from_file(tokenizer_path)

        except Exception as e:
            # Fallback: try without authentication
            try:
                tokenizer_path = hf_hub_download(
                    repo_id=self.model,
                    filename="tokenizer.json"
                )
                return Tokenizer.from_file(tokenizer_path)
            except Exception as fallback_e:
                raise ValueError(
                    f"Failed to load tokenizer for {self.model}: {str(e)} | Fallback error: {str(fallback_e)}")

    def count_message_tokens(self, message: Dict[str, str]) -> int:
        """
        Count tokens in a single message.
        """
        num_tokens = self.tokens_per_message
        for _, value in message.items():
            value_str = str(value)
            encoding = self.tokenizer.encode(value_str, add_special_tokens=False)
            num_tokens += len(encoding.ids)
        return num_tokens

    def count_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        Count total tokens in a list of messages.
        """
        try:
            num_tokens = 0
            for message in messages:
                num_tokens += self.count_message_tokens(message)
            # Add 3 tokens for the assistant's reply format (as per OpenAI API)
            num_tokens += 3
            return num_tokens
        except Exception as e:
            raise ValueError(f"Error counting tokens: {str(e)}")

    def adjust_max_tokens(self, user_message: List[Dict[str, str]], max_tokens: int) -> int:
        """
        Calculate remaining tokens based on max_tokens and message tokens.
        """
        try:
            message_tokens = self.count_tokens(user_message)
            remaining_tokens = max_tokens - message_tokens
            if remaining_tokens < 0:
                raise ValueError(f"Message tokens ({message_tokens}) exceed max tokens ({max_tokens})")
            return remaining_tokens
        except Exception as e:
            raise ValueError(f"Error adjusting max tokens: {str(e)}")
