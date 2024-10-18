import argparse
import yaml
import os

from api import GroqClient, Gitlab_api, Github_api
from src import OPTIONS, DisplayChoices, Commit, Prompts, Merge_requests


class Main:
    model = None
    temperature = None
    max_tokens = None
    target_branch = None
    platform = None

    def __init__(self):
        self.args = self.parse_arguments()

        self.Commit = Commit()
        self.Merge_requests = Merge_requests()
        self.Prompt = Prompts()
        self.DisplayChoices = DisplayChoices()

        self.Gitlab = Gitlab_api()
        self.Github = Github_api()

        self.load_config()
        self.init_groq_client()

        if self.args.command == 'merge':
            self.do_merge_request()
        elif self.args.command == 'commit':
            self.do_commit()
        else:
            print("Please specify a command: merge or commit")

    def parse_arguments(self):
        parser = argparse.ArgumentParser(
            description="Git-AI (gai): Automate your git messages")

        # Hepler text
        subparsers = parser.add_subparsers(
            dest='command', help='Available commands')

        # Commands
        merge_parser = subparsers.add_parser(
            'merge', help='Execute an automated merge request')

        commit_parser = subparsers.add_parser(
            'commit', help='Execute an automated commit')

        # Common arguments
        for p in [merge_parser, commit_parser]:
            p.add_argument('--platform', '-p', type=str,
                           help='Specify the platform (supported: gitlab or github)')
            p.add_argument('--model', '-mo', type=str,
                           help='Override the model specified in config')
            p.add_argument('--temperature', '-t', type=float,
                           help='Override the temperature specified in config')
            p.add_argument('--max-tokens', '-mt', type=int,
                           help='Override the max_tokens specified in config')
            p.add_argument('--target-branch', '-tb', type=str,
                           help='Specify the target branch for merge requests')

        return parser.parse_args()

    def load_config(self):
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)

        self.model = self.args.model or config['model']
        self.temperature = self.args.temperature or config['temperature']
        self.max_tokens = self.args.max_tokens or config['max_tokens']
        self.target_branch = self.args.target_branch or config['target_branch']
        self.platform = self.args.platform or config['platform']

    def init_groq_client(self):
        self.groq_chat_client = GroqClient(
            api_key=self.get_api_key(),
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens

        )

    # migrate this to groq_api.py
    def get_api_key(self):
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key is None:
            raise ValueError(
                "GROQ_API_KEY is not set, please set it in your environment variables")
        return api_key

    # make this dynamic (gitlab/github)
    def do_merge_request(self):
        title = ""

        commits = self.Merge_requests.get_commits(
            target_branch=self.target_branch,
            source_branch=self.Gitlab.get_current_branch())  # TODO: fix this func

        # migrate prompot logic to merge_request.py
        build_prompt = self.Prompt.build_merge_request_title_prompt(commits)

        description = self.Merge_requests.format_commits(commits)

        print(build_prompt)
        print(f"token count: {len(build_prompt.split())}")

        while title is OPTIONS["TRY_AGAIN"] or title == "":
            response = self.groq_chat_client.get_chat_completion(build_prompt)
            print(response)
            title = self.DisplayChoices.run(response)
            print(title)

        if title is OPTIONS["EXIT"]:
            print("Exiting...")
            return

        print("Creating merge request with...")
        print(f"Title: {title}")
        print(f"Description: {description}")

        if self.platform == "gitlab":
            self.Gitlab.create_merge_request(
                title=title,
                description=description)
        elif self.platform == "github":
            self.Github.create_pull_request(
                title=title,
                body=description)
        else:
            print("Please specify a platform, you can use the --platform flag")
            return

    def do_commit(self):
        git_diffs = self.Commit.get_diffs()
        build_prompt = self.Prompt.build_commit_message_prompt(
            git_diffs)

        commit_message = ""
        # print(build_prompt)
        print(f"Token count: {len(build_prompt.split())}")

        while commit_message is OPTIONS["TRY_AGAIN"] or commit_message == "":
            response = self.groq_chat_client.get_chat_completion(build_prompt)
            print(response)
            commit_message = self.DisplayChoices.run(response)
            print(commit_message)

        if commit_message is OPTIONS["EXIT"]:
            print("Exiting...")
            return

        self.Commit.commit_changes(commit_message)


if __name__ == "__main__":
    Main()
