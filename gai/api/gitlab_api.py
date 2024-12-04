import os
import requests
import yaml
import subprocess

from gai.src import Merge_requests, ConfigManager, get_app_name


class Gitlab_api():
    def __init__(self):
        self.load_config()
        self.Merge_requests = Merge_requests().get_instance()

    def load_config(self):
        config_manager = ConfigManager(get_app_name())
        self.target_branch = config_manager.get_config('target_branch')
        self.assignee_id = config_manager.get_config('assignee_id')


    def get_api_url(self) -> str:
        gitlab_domain = self.Merge_requests.get_remote_url()
        repo_owner = self.Merge_requests.get_repo_owner_from_remote_url()
        repo_name = self.Merge_requests.get_repo_from_remote_url()
        return f"https://{gitlab_domain}/api/v4/projects/{repo_owner}%2F{repo_name}/merge_requests"

    def get_api_key(self):
        api_key = os.environ.get("GITLAB_PRIVATE_TOKEN")

        if api_key is None:
            raise ValueError(
                "GITLAB_PRIVATE_TOKEN is not set, please set it in your environment variables")

        return api_key

    def get_current_branch(self) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        return result.stdout.strip()

    def get_existing_merge_request(self, source_branch: str) -> dict:
        """
        Get existing merge request for the current branch.
        """
        api_key = self.get_api_key()

        response = requests.get(
            f"{self.get_api_url()}",
            headers={"PRIVATE-TOKEN": api_key},
            params={
                "source_branch": source_branch,
                "state": "opened"
            }
        )

        if response.status_code == 201:
            mrs = response.json()
            return mrs[0] if mrs else None
        return None

    def update_merge_request(self, mr_id: int, title: str, description: str) -> None:
        """
        Update an existing merge request.
        """
        api_key = self.get_api_key()

        data = {
            "title": title,
            "description": description
        }

        response = requests.put(
            f"{self.get_api_url()}/{mr_id}",
            headers={"PRIVATE-TOKEN": api_key},
            json=data
        )

        if response.status_code == 201:
            print("Merge request updated successfully.")
        else:
            print(f"Failed to update merge request: {response.status_code}")
            print(f"Response text: {response.text}")

    def create_merge_request(self, title: str, description: str) -> None:
        api_key = self.get_api_key()
        source_branch = self.get_current_branch()

        existing_mr = self.get_existing_merge_request(source_branch)

        if existing_mr:
            print(f"A merge request already exists: {existing_mr['web_url']}")
            self.update_merge_request(
                mr_id=existing_mr['iid'],
                title=title,
                description=description
            )

        else:
            data = {
                "source_branch": source_branch,
                "target_branch": self.target_branch,
                "title": title,
                "description": description,
                "assignee_id": self.assignee_id
            }

            response = requests.post(
                f"{self.get_api_url()}",
                headers={"PRIVATE-TOKEN": api_key},
                json=data
            )

            if response.status_code == 201:
                print("Merge request created successfully.")
            else:
                print(f"Failed to create merge request: {response.status_code}")
                print(f"Response text: {response.text}")
