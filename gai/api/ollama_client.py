
import os
from typing import Dict, List
from langchain_ollama import ChatOllama

from gai.src import Prompts, print_tokens
from gai.api.token_counter import TokenCounter
from gai.src.utils import create_system_message, get_api_huggingface_key, validate_messages


class OllamaClient:
    def __init__(self,
                 model: str,
                 temperature: int,
                 max_tokens: int) -> str:

        self.client = ChatOllama(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def get_system_prompt(self):
        return Prompts().build_commit_message_system_prompt()

    # Invoke the ollama client
    def get_chat_completion(self,
                            user_message: List[Dict[str, str]]
                            ):

        validate_messages(messages=user_message)

        ai_response = self.client.invoke(user_message)
        return ai_response.content
