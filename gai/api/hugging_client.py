
import os
from huggingface_hub import InferenceClient


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

    def adjust_max_tokens(self, user_message) -> int:
        return self.max_tokens - len(user_message)

    def get_chat_completion(self, user_message):
        adjusted_max_tokens = self.adjust_max_tokens(user_message)

        print(f"user_message: {user_message}")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                # TODO: migrate initial prompt to system msg
                # {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_message},
            ],
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
