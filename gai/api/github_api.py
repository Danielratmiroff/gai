import os
import requests
import yaml
import subprocess

from gai.src import Merge_requests, ConfigManager, get_app_name


class Github_api():
    def __init__(self):
        self.Merge_requests = Merge_requests().get_instance()
        self.load_config()

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

    def get_current_branch(self) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    def create_pull_request(self, title: str, body: str) -> None:
        api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/pulls"

        source_branch = self.get_current_branch()
        api_key = self.get_api_key()

        existing_pr = self.get_existing_pr(api_url=api_url)

        if existing_pr:
            pr_number = existing_pr['number']
            existing_pr_url = f"{api_url}/{pr_number}"
            print(f"A pull request already exists: {existing_pr['html_url']}")
            self.update_pull_request(
                api_url=existing_pr_url,
                title=title,
                body=body
            )
        else:
            data = {
                "title": title,
                "head": source_branch,
                "base": self.target_branch,
                "body": body
            }

            response = requests.post(
                api_url,
                headers={
                    "Authorization": f"token {api_key}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json=data
            )

            if response.status_code == 201:
                print("Pull request created successfully.")
                pr_info = response.json()
                print(f"Pull request URL: {pr_info['html_url']}")
            else:
                print(f"Failed to create pull request: {response.status_code}")
                error_message = response.json()
                print(f"Error message: {error_message}")

    def get_existing_pr(self, api_url: str) -> dict:
        """
        Get existing pull request for the current branch.
        """
        api_key = self.get_api_key()
        source_branch = self.get_current_branch()

        response = requests.get(
            api_url,
            headers={
                "Authorization": f"token {api_key}",
                "Accept": "application/vnd.github.v3+json"
            },
            params={
                "head": f"{self.repo_owner}:{source_branch}",
                "state": "open"
            }
        )

        if response.status_code == 200:
            prs = response.json()
            return prs[0] if prs else None
        return None

    def update_pull_request(self, api_url: str, body: str, title: str) -> None:
        """
        Update an existing pull request.
        """
        api_key = self.get_api_key()

        data = {
            "title": title,
            "body": body
        }

        response = requests.patch(
            api_url,
            headers={
                "Authorization": f"token {api_key}",
                "Accept": "application/vnd.github.v3+json"
            },
            json=data
        )

        if response.status_code == 200:
            print("Pull request updated successfully.")
        else:
            print(f"Failed to update pull request: {response.status_code}")
            error_message = response.json()
            print(f"Error message: {error_message}")
