
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

    def get_chat_completion(self, user_message):
        output = self.client.chat.completions.create(
            model=self.model,
            messages=[
                # {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",
                 "content": user_message},
            ],
            stream=True,
            max_tokens=self.max_tokens,
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
