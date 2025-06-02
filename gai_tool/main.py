from gai_tool.src import DisplayChoices, Commits, Prompts, Merge_requests, ConfigManager, get_app_name, get_attr_or_default, get_current_branch, push_changes, get_package_version, attr_is_defined, GROQ_MODELS, HUGGING_FACE_MODELS, DEFAULT_CONFIG, OLLAMA_MODELS, GEMINI_MODELS, get_ticket_identifier
from gai_tool.api import GroqClient, Gitlab_api, Github_api, HuggingClient, OllamaClient, GeminiClient
from gai_tool.src.utils import create_system_message, create_user_message
import argparse
import logging


# Suppress transformers logging as we don't need it
logging.getLogger("transformers").setLevel(logging.ERROR)


class Main:
    def run(self):
        self.args = self.parse_arguments()
        self.remote_repo = get_attr_or_default(self.args, 'remote', 'origin')

        # Initialize singleton
        Merge_requests.initialize(remote_name=self.remote_repo)
        self.ConfigManager = ConfigManager(get_app_name())
        self.load_config()

        self.Commits = Commits()
        self.Prompt = Prompts()
        self.DisplayChoices = DisplayChoices()

        # Version
        if attr_is_defined(self.args, 'version') and self.args.version is True:
            print(f"v{get_package_version(get_app_name())}")
            return

        self.ai_client = self.init_ai_client()

        # Main commands
        if self.args.command == 'merge':
            if self.args.push:
                push_changes(self.remote_repo)
            self.do_merge_request()
        elif self.args.command == 'commit':
            self.do_commit()
        elif self.args.command == 'init':
            self.ConfigManager.init_local_config()
        else:
            print("Please specify a command: init, merge, or commit")

    def load_config(self):
        # AI model arguments
        self.temperature = get_attr_or_default(self.args, 'temperature', self.ConfigManager.get_config('temperature'))
        # self.max_tokens = get_attr_or_default(self.args, 'max_tokens', self.ConfigManager.get_config('max_tokens'))
        self.target_branch = get_attr_or_default(
            self.args, 'target_branch', self.ConfigManager.get_config('target_branch'))

        # API interface
        self.interface = get_attr_or_default(self.args, 'interface', self.ConfigManager.get_config('interface'))

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Git-AI (gai): Automate your git messages")

        # Version
        parser.add_argument('-v', '--version', action='store_true',
                            help='Display the version of the tool')

        # Helper text
        subparsers = parser.add_subparsers(dest='command',
                                           help='Available commands')

        # Init config
        init_parser = subparsers.add_parser('init',
                                            help='Initialize a local configuration file')

        # Merge request
        merge_parser = subparsers.add_parser('merge',
                                             help='Execute an automated merge request')

        merge_parser.add_argument('remote', nargs='?',
                                  help='Specify the remote git url (e.g., origin, upstream)')

        merge_parser.add_argument('--push', '-p', action='store_true',
                                  help='Push changes to remote before creating a merge request')

        merge_parser.add_argument('--target-branch', '-tb', type=str,
                                  help='Specify the target branch for merge requests')
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
            # p.add_argument('--max-tokens', '-mt', type=int,
            #    help='Override the max_tokens specified in config')
            # p.add_argument('--target-branch', '-tb', type=str,
            #                help='Specify the target branch for merge requests')
            p.add_argument('--interface', '-i', type=str,
                           help='Specify the client api to use (e.g., groq, huggingface)')

        return parser.parse_args()

    def init_ai_client(self):
        print(f"Using {self.interface} as ai interface")
        match self.interface:
            case "huggingface":
                model = HUGGING_FACE_MODELS[0]

                client = HuggingClient(
                    model=model.model_name,
                    temperature=self.temperature,
                    max_tokens=model.max_tokens
                )

            case "groq":
                model = GROQ_MODELS[0]

                client = GroqClient(
                    model=model.model_name,
                    temperature=self.temperature,
                    max_tokens=model.max_tokens
                )

            case "google":
                model = GEMINI_MODELS[0]

                client = GeminiClient(
                    model=model.model_name,
                    temperature=self.temperature,
                    max_output_tokens=model.max_tokens
                )

            # Default to ollama
            case _:
                model = OLLAMA_MODELS[4]

                client = OllamaClient(
                    model=model.model_name,
                    temperature=self.temperature,
                    max_tokens=model.max_tokens
                )

        # Set as default if not already set
        if self.ConfigManager.get_config('interface') != self.interface:
            self.ConfigManager.update_config('interface', self.interface)

        return client.get_chat_completion

    def do_merge_request(self):
        mr = Merge_requests().get_instance()

        platform = mr.get_remote_platform()
        current_branch = get_current_branch()
        system_prompt = self.Prompt.build_merge_title_system_prompt()
        system_description_prompt = self.Prompt.build_merge_description_system_prompt()

        # Get description
        try:
            commits = self.Commits.get_commits(
                remote_repo=self.remote_repo,
                target_branch=self.target_branch,
                source_branch=current_branch)
        except Exception as e:
            print(f"Error fetching commits: {e}")
            return

        all_commits = self.Commits.format_commits(commits)

        # Get title
        try:
            selected_title = self.DisplayChoices.render_choices_with_try_again(
                user_msg=all_commits,
                sys_prompt=system_prompt,
                ai_client=self.ai_client)

            # Get description
            mr_description = self.ai_client(
                user_message=[
                    create_system_message(system_description_prompt),
                    create_user_message(all_commits)
                ]
            )
        except Exception as e:
            print(f"Exiting... {e}")
            return

        # Get ticket identifier
        ticket_id = get_ticket_identifier(current_branch, self.ai_client)
        if ticket_id:
            selected_title = f"{ticket_id} - {selected_title}"

        print("Creating pull request...")
        print(f"From {current_branch} to {self.target_branch}")
        print(f"Title: {selected_title}")

        match platform:
            case "gitlab":
                # Lazy initialization of GitLab API client
                try:
                    gitlab_client = Gitlab_api()
                    gitlab_client.create_merge_request(
                        title=selected_title,
                        description=mr_description,
                        target_branch=self.target_branch)
                except Exception as e:
                    print(f"Failed to create GitLab merge request: {e}")
                    print("Please check your GITLAB_PRIVATE_TOKEN and project access.")
                    return

            case "github":
                # Lazy initialization of GitHub API client
                try:
                    github_client = Github_api()
                    github_client.create_pull_request(
                        title=selected_title,
                        body=mr_description,
                        target_branch=self.target_branch)
                except Exception as e:
                    print(f"Failed to create GitHub pull request: {e}")
                    print("Please check your GitHub token and repository access.")
                    return
            case _:
                raise ValueError(
                    "Platform not supported. Only github and gitlab are supported.")

    def do_commit(self):
        if self.args.all:
            self.Commits.stage_changes()

        git_diffs = self.Commits.get_diffs()

        system_prompt = self.Prompt.build_commit_message_system_prompt()

        try:
            selected_commit = self.DisplayChoices.render_choices_with_try_again(
                user_msg=git_diffs,
                sys_prompt=system_prompt,
                ai_client=self.ai_client
            )
        except Exception as e:
            print(f"Exiting... {e}")
            return

        # Get ticket identifier and prepend to commit message
        current_branch = get_current_branch()
        ticket_id = get_ticket_identifier(current_branch, self.ai_client)
        if ticket_id:
            selected_commit = f"{ticket_id} - {selected_commit}"

        self.Commits.commit_changes(selected_commit)


def main():
    app = Main()
    app.run()


if __name__ == "__main__":
    main()
