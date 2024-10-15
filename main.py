import yaml
import os
import yaml

from groq import Groq

from api.groq_api import GroqClient
from src.commit import Commit
from src.prompts import Prompts


class Main:
    model = None
    temperature = None
    max_tokens = None
    api_key = None

    def __init__(self):
        self.Commit = Commit()
        self.Prompt = Prompts()

        self.loadConfig()
        self.run()

    def loadConfig(self):
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)

        self.model = config['model']
        self.temperature = config['temperature']
        self.max_tokens = config['max_tokens']

    def getApiKey(self):
        api_key = os.environ.get("GROQ_API_KEY")

        if api_key is None:
            raise ValueError(
                "GROQ_API_KEY is not set, please set it in your environment variables")

        return self.api_key

    def run(self):
        groq_chat_client = GroqClient(
            self.getApiKey(), self.model, self.temperature, self.max_tokens)

        git_diffs = self.Commit.get_diffs()
        build_prompt = self.Prompt.build_commit_message_prompt(git_diffs)

        print(build_prompt)
        print(f"token count: {len(build_prompt.split())}")

        response = groq_chat_client.get_chat_completion(build_prompt)
        print(response)


if __name__ == "__main__":
    Main()
