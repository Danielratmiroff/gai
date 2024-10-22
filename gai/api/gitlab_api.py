import os
import requests
import yaml
import subprocess

from gai.src import Merge_requests


class Gitlab_api():
    def __init__(self):
        self.load_config()
        self.Merge_requests = Merge_requests()

    def load_config(self):
        with open("gai/config.yaml", "r") as file:
            config = yaml.safe_load(file)

        self.target_branch = config['target_branch']
        self.assignee = config['gitlab_assignee_id']

    def construct_project_url(self) -> str:
        repo_owner = self.Merge_requests.get_repo_owner_from_remote_url()
        repo_name = self.Merge_requests.get_repo_from_remote_url()
        return f"{repo_owner}%2F{repo_name}"

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

    def create_merge_request(self, title: str, description: str) -> None:
        gitlab_url = self.Merge_requests.get_remote_url()

        project = self.construct_project_url()
        api_key = self.get_api_key()
        source_branch = self.get_current_branch()

        data = {
            "source_branch": source_branch,
            "target_branch": self.target_branch,
            "title": title,
            "description": description,
            "assignee_id": self.assignee
        }

        response = requests.post(
            f"https://{gitlab_url}/api/v4/projects/{project}/merge_requests",
            headers={"PRIVATE-TOKEN": api_key},
            json=data
        )

        if response.status_code == 201:
            print("Merge request created successfully:", response.status_code)
        else:
            print(f"Failed to create merge request: {response.status_code}")
            print(f"Response text: {response.text}")
