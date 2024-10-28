import os
from groq import Groq

from gai.src import Prompts, print_tokens


class GroqClient:
    def __init__(self,
                 model: str,
                 temperature: int,
                 max_tokens: int) -> str:

        self.client = Groq(api_key=self.get_api_key())
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def get_system_prompt(self):
        return Prompts().build_commit_message_system_prompt()

    def get_chat_completion(self, user_message, system_prompt):

        print_tokens(system_prompt, user_message, self.max_tokens)

        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "assistant",
                    "content": self.get_system_prompt(),
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            top_p=1,
            stream=False,
            stop=None,
        )
        return chat_completion.choices[0].message.content

    def get_api_key(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key is None:
            raise ValueError(
                "GROQ_API_KEY is not set, please set it in your environment variables")
        return api_key
