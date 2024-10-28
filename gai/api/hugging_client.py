
import os
from typing import Dict, List
from huggingface_hub import InferenceClient

from gai.src import Prompts, print_tokens
from gai.src.utils import create_system_message


class HuggingClient:
    def __init__(self,
                 model: str,
                 temperature: int,
                 max_tokens: int) -> str:

        self.client = InferenceClient(
            api_key=self.get_api_key()
        )
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def run(self):
        print("Huggingface client running")

    def adjust_max_tokens(self, user_message) -> int:
        return self.max_tokens - len(user_message)

    def get_system_prompt(self):
        return Prompts().build_commit_message_system_prompt()

    def get_chat_completion(self,
                            user_message: List[Dict[str, str]],
                            system_prompt: str
                            ):
        print_tokens(system_prompt, user_message, self.max_tokens)

        adjusted_max_tokens = self.adjust_max_tokens(user_message)

        # Append system prompt to user message
        system_prompt = create_system_message(system_prompt)
        messages = [system_prompt] + user_message

        response = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            max_tokens=adjusted_max_tokens,
            temperature=self.temperature,
            stream=False,
        )
        return response.choices[0].message.content

    def get_api_key(self):
        api_key = os.environ.get("HUGGING_FACE_TOKEN")
        if api_key is None:
            raise ValueError(
                "HUGGING_FACE_TOKEN is not set, please set it in your environment variables")
        return api_key
