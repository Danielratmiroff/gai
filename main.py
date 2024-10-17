import yaml
import os
import yaml

from groq import Groq

from api.groq_api import GroqClient
from src.display_choices import OPTIONS, DisplayChoices
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
        self.DisplayChoices = DisplayChoices()

        self.load_config()
        self.init_groq_client()
        self.run()

    def init_groq_client(self):
        self.groq_chat_client = GroqClient(
            self.get_api_key(), self.model, self.temperature, self.max_tokens)

    def load_config(self):
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)

        self.model = config['model']
        self.temperature = config['temperature']
        self.max_tokens = config['max_tokens']

    def get_api_key(self):
        api_key = os.environ.get("GROQ_API_KEY")

        if api_key is None:
            raise ValueError(
                "GROQ_API_KEY is not set, please set it in your environment variables")

        return self.api_key

    def run(self):
        commit_message = ""
        git_diffs = self.Commit.get_diffs()
        build_prompt = self.Prompt.build_commit_message_prompt(git_diffs)

        # print(build_prompt)
        print(f"token count: {len(build_prompt.split())}")

        while commit_message is not OPTIONS["TRY_AGAIN"]:
            response = self.groq_chat_client.get_chat_completion(build_prompt)
            commit_message = self.DisplayChoices.run(response)
            print(commit_message)

        if commit_message is OPTIONS["EXIT"]:
            print("Exiting...")
            return

        self.Commit.commit_changes(commit_message)


if __name__ == "__main__":
    Main()
