import logging
import warnings
import os

# Disable all warnings
warnings.filterwarnings('ignore')

# Disable specific transformers warnings
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = 'true'

# Set logging level to ERROR
logging.getLogger("transformers").setLevel(logging.ERROR)

from typing import List, Dict, Optional
from transformers import AutoTokenizer
import os

from gai.src.utils import get_api_huggingface_key


# Token counter only supports Huggingface models for now
# TODO: Add support for GROQ models
class TokenCounter:
    def __init__(self,
                 model: str
                 ):
        """
        Initialize token counter with specified model using transformers tokenizer.

        Parameters:
        - model: The name or path of the model.
        """
        self.tokens_per_message = 3  # Every message follows {role/name, content}

        # Attempt to load token from environment variable
        hf_token = get_api_huggingface_key()
        if hf_token:
            self.tokenizer = AutoTokenizer.from_pretrained(
                model,
                token=hf_token
            )
        else:
            # Attempt to load without authentication
            self.tokenizer = AutoTokenizer.from_pretrained(model)

    def count_message_tokens(self, message: Dict[str, str]) -> int:
        """
        Count tokens in a single message.
        """
        num_tokens = self.tokens_per_message
        for _, value in message.items():
            value_str = str(value)
            tokens = self.tokenizer.encode(value_str, add_special_tokens=False)
            num_tokens += len(tokens)
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
