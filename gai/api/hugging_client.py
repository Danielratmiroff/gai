
import os
from huggingface_hub import InferenceClient

MAX_API_TOKENS = 8192


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
        input = len(user_message) + self.max_tokens
        if input > MAX_API_TOKENS:
            return MAX_API_TOKENS - len(user_message)

    def get_chat_completion(self, user_message):
        include_input_as_max_tokens = self.adjust_max_tokens(user_message)

        output = self.client.chat.completions.create(
            model=self.model,
            messages=[
                # {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",
                 "content": user_message},
            ],
            stream=True,
            max_tokens=include_input_as_max_tokens,
            temperature=self.temperature,
        )

        for chunk in output:
            return chunk.choices[0].delta.content

    def get_api_key(self):
        api_key = os.environ.get("HUGGING_FACE_TOKEN")
        if api_key is None:
            raise ValueError(
                "HUGGING_FACE_TOKEN is not set, please set it in your environment variables")
        return api_key
