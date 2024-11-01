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
        repo_owner = self.Merge_requests.get_repo_owner_from_remote_url()
        repo_name = self.Merge_requests.get_repo_from_remote_url()

        source_branch = self.get_current_branch()
        api_key = self.get_api_key()

        data = {
            "title": title,
            "head": source_branch,
            "base": self.target_branch,
            "body": body
        }

        response = requests.post(
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls",
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
            error_message = response.json()
            if response.status_code == 422 and 'A pull request already exists' in error_message.get('message', ''):
                existing_pr_url = error_message['errors'][0]['message'].split()[-1]
                print(f"A pull request already exists: {existing_pr_url}")
                self.update_pull_request(existing_pr_url, body)
            else:
                print(f"Failed to create pull request: {response.status_code}")
                print(f"Error message: {error_message}")
    def update_pull_request(self, pr_url: str, body: str) -> None:
        api_key = self.get_api_key()
        response = requests.patch(
            pr_url,
            headers={
                "Authorization": f"token {api_key}",
                "Accept": "application/vnd.github.v3+json"
            },
            json={"body": body}
        )

        if response.status_code == 200:
            print("Pull request updated successfully.")
        else:
            print(f"Failed to update pull request: {response.status_code}")
            error_message = response.json()
            print(f"Error message: {error_message}")
