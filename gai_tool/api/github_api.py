import os
import subprocess
from github import Github, GithubException

from gai_tool.src import Merge_requests, ConfigManager, get_app_name


class Github_api():
    def __init__(self):
        self.Merge_requests = Merge_requests().get_instance()
        self.load_config()
        self._github = None

    def load_config(self):
        config_manager = ConfigManager(get_app_name())

        self.repo_owner = self.Merge_requests.get_repo_owner_from_remote_url()
        self.repo_name = self.Merge_requests.get_repo_from_remote_url()
        self.target_branch = config_manager.get_config('target_branch')

    def get_api_key(self):
        api_key = os.environ.get("GITHUB_TOKEN")

        if api_key is None:
            raise ValueError(
                "GITHUB_TOKEN is not set. Please set it in your environment variables.")

        return api_key

    @property
    def github(self):
        """Lazy initialization of GitHub client."""
        if self._github is None:
            api_key = self.get_api_key()
            self._github = Github(api_key)
        return self._github

    @property
    def repo(self):
        """Get the GitHub repository object."""
        return self.github.get_repo(f"{self.repo_owner}/{self.repo_name}")

    def get_current_branch(self) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    def create_pull_request(self, title: str, body: str, target_branch: str = None) -> None:
        source_branch = self.get_current_branch()

        # Use provided target_branch or fall back to config
        target_branch_to_use = target_branch if target_branch is not None else self.target_branch

        try:
            existing_pr = self.get_existing_pr()

            if existing_pr:
                print(f"A pull request already exists: {existing_pr.html_url}")
                self.update_pull_request(
                    existing_pr,
                    title=title,
                    body=body
                )
            else:
                pr = self.repo.create_pull(
                    title=title,
                    body=body,
                    head=source_branch,
                    base=target_branch_to_use
                )

                print("Pull request created successfully.")
                print(f"Pull request URL: {pr.html_url}")

        except GithubException as e:
            print(f"Failed to create pull request: {e.status}")
            print(f"Error message: {e.data}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

    def get_existing_pr(self):
        """
        Get existing pull request for the current branch.
        Returns the PullRequest object if found, None otherwise.
        """
        try:
            source_branch = self.get_current_branch()

            # Get open pull requests from the current branch
            pulls = self.repo.get_pulls(
                state='open',
                head=f"{self.repo_owner}:{source_branch}"
            )

            # Return the first matching PR, if any
            for pr in pulls:
                return pr

            return None

        except GithubException as e:
            print(f"Error fetching pull requests: {e.status}")
            print(f"Error message: {e.data}")
            return None

    def update_pull_request(self, pr, title: str, body: str) -> None:
        """
        Update an existing pull request.

        Args:
            pr: PullRequest object from PyGithub
            title: New title for the PR
            body: New body for the PR
        """
        try:
            pr.edit(title=title, body=body)
            print("Pull request updated successfully.")

        except GithubException as e:
            print(f"Failed to update pull request: {e.status}")
            print(f"Error message: {e.data}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
