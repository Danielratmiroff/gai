import yaml
import os

from api import GroqClient, Gitlab_api
from src import OPTIONS, DisplayChoices, Commit, Prompts, Merge_requests


class Main:
    model = None
    temperature = None
    max_tokens = None
    target_branch = None

    def __init__(self):
        self.Commit = Commit()
        self.Merge_requests = Merge_requests()
        self.Prompt = Prompts()
        self.DisplayChoices = DisplayChoices()
        self.Gitlab = Gitlab_api()

        self.load_config()
        self.init_groq_client()
        self.run_merge_request()
        # self.run()

    def init_groq_client(self):
        self.groq_chat_client = GroqClient(
            self.get_api_key(), self.model, self.temperature, self.max_tokens)

    def load_config(self):
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)

        self.model = config['model']
        self.temperature = config['temperature']
        self.max_tokens = config['max_tokens']
        self.target_branch = config['target_branch']

    # migrate this to groq_api.py
    def get_api_key(self):
        api_key = os.environ.get("GROQ_API_KEY")

        if api_key is None:
            raise ValueError(
                "GROQ_API_KEY is not set, please set it in your environment variables")

        return api_key

    def run_merge_request(self):
        description = self.Merge_requests.create_description(
            self.target_branch)
        self.Gitlab.create_merge_request(description)

    def run(self):
        git_diffs = self.Commit.get_diffs()
        build_prompt = self.Prompt.build_commit_message_prompt(git_diffs)

        commit_message = ""

        print(build_prompt)
        print(f"token count: {len(build_prompt.split())}")

        while commit_message is OPTIONS["TRY_AGAIN"] or commit_message == "":
            response = self.groq_chat_client.get_chat_completion(build_prompt)
            commit_message = self.DisplayChoices.run(response)
            print(commit_message)

        if commit_message is OPTIONS["EXIT"]:
            print("Exiting...")
            return

        self.Commit.commit_changes(commit_message)


if __name__ == "__main__":
    Main()
