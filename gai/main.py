import argparse
from dataclasses import dataclass
import subprocess
import yaml
import os

from gai.api import GroqClient, Gitlab_api, Github_api, HuggingClient
from gai.src import DisplayChoices, Commits, Prompts, Merge_requests, ConfigManager, get_app_name, get_attr_or_default, get_current_branch, push_changes, get_package_version, attr_is_defined, GROQ_MODELS, HUGGING_FACE_MODELS, DEFAULT_CONFIG


class Main:
    def run(self):
        self.args = self.parse_arguments()

        self.Commits = Commits()
        self.Prompt = Prompts()
        self.DisplayChoices = DisplayChoices()

        self.Gitlab = Gitlab_api()
        self.Github = Github_api()

        self.ConfigManager = ConfigManager(get_app_name())

        self.load_config()
        self.ai_client = self.init_ai_client()

        # Version
        if attr_is_defined(self.args, 'version') and self.args.version is True:
            print(f"v{get_package_version(get_app_name())}")
            return

        # Main commands
        if self.args.command == 'merge':
            if self.args.push:
                push_changes(self.remote_repo)
            self.do_merge_request()
        elif self.args.command == 'commit':
            self.do_commit()
        else:
            print("Please specify a command: merge or commit")

    def load_config(self):
        # AI model arguments
        self.temperature = get_attr_or_default(self.args, 'temperature', self.ConfigManager.get_config('temperature'))
        self.max_tokens = get_attr_or_default(self.args, 'max_tokens', self.ConfigManager.get_config('max_tokens'))
        self.target_branch = get_attr_or_default(
            self.args, 'target_branch', self.ConfigManager.get_config('target_branch'))

        # API interface
        self.interface = get_attr_or_default(self.args, 'interface', self.ConfigManager.get_config('interface'))

        # Other arguments
        self.remote_repo = get_attr_or_default(self.args, 'remote', 'origin')

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Git-AI (gai): Automate your git messages")

        # Version
        parser.add_argument('-v', '--version', action='store_true',
                            help='Display the version of the tool')

        # Helper text
        subparsers = parser.add_subparsers(dest='command',
                                           help='Available commands')

        # Merge request
        merge_parser = subparsers.add_parser('merge',
                                             help='Execute an automated merge request')

        merge_parser.add_argument('remote', nargs='?',
                                  help='Specify the remote git url (e.g., origin, upstream)')

        merge_parser.add_argument('--push', '-p', action='store_true',
                                  help='Push changes to remote after creating merge request')
        # Commit
        commit_parser = subparsers.add_parser('commit', help='Execute an automated commit')

        commit_parser.add_argument('--all', '-a', action='store_true',
                                   help='Stage all changes before committing')

        # Common arguments
        for p in [merge_parser, commit_parser]:
            # AI model arguments
            # p.add_argument('--model', '-mo', type=str,
            #    help='Override the model specified in config')
            p.add_argument('--temperature', '-t', type=float,
                           help='Override the temperature specified in config')
            p.add_argument('--max-tokens', '-mt', type=int,
                           help='Override the max_tokens specified in config')
            p.add_argument('--target-branch', '-tb', type=str,
                           help='Specify the target branch for merge requests')
            p.add_argument('--interface', '-i', type=str,
                           help='Specify the client api to use (e.g., groq, huggingface)')

        return parser.parse_args()

    def init_ai_client(self):
        match self.interface:
            case "huggingface":
                print("Using Huggingface as ai interface")

                client = HuggingClient(
                    model=HUGGING_FACE_MODELS[0],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                self.ConfigManager.update_config('interface', 'huggingface')

            case _:
                print("Using Groq as ai interface")

                client = GroqClient(
                    model=GROQ_MODELS[0],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )

                self.ConfigManager.update_config('interface', 'groq')

        return client.get_chat_completion

    def do_merge_request(self):
        # Initialize singleton
        Merge_requests.initialize(remote_name=self.remote_repo)

        mr = Merge_requests().get_instance()

        platform = mr.get_remote_platform()
        current_branch = get_current_branch()

        commits = self.Commits.get_commits(
            remote_repo=self.remote_repo,
            target_branch=self.target_branch,
            source_branch=current_branch)

        prompt = self.Prompt.build_merge_request_title_prompt(commits)

        description = self.Commits.format_commits(commits)

        print(prompt)
        print(f"token count: {len(prompt.split())}")

        try:
            selected_title = self.DisplayChoices.render_choices_with_try_again(
                prompt=prompt,
                ai_client=self.ai_client)
        except Exception as e:
            print(f"Exiting... {e}")
            return

        print("Creating merge request with...")
        print(f"Title: {selected_title}")
        print(f"Description: {description}")

        print("Platform: ", platform)

        match platform:
            case "gitlab":
                self.Gitlab.create_merge_request(
                    title=selected_title,
                    description=description)

            case "github":
                self.Github.create_pull_request(
                    title=selected_title,
                    body=description)
            case _:
                raise ValueError(
                    "Platform not supported. Only github and gitlab are supported.")

    def do_commit(self):
        if self.args.all:
            self.Commits.stage_changes()

        git_diffs = self.Commits.get_diffs()

        prompt = self.Prompt.build_commit_message_prompt(
            git_diffs)

        # print(build_prompt)
        print(f"Token count: {len(prompt.split())}")

        try:
            selected_commit = self.DisplayChoices.render_choices_with_try_again(
                prompt=prompt,
                ai_client=self.ai_client)
        except Exception as e:
            print(f"Exiting... {e}")
            return

        print("selected_commit", selected_commit)
        self.Commits.commit_changes(selected_commit)


def main():
    app = Main()
    app.run()


if __name__ == "__main__":
    main()
