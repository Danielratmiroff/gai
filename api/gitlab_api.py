import os
import requests
import yaml
import subprocess


class Gitlab_api():
    def __init__(self):
        self.load_config()

    def load_config(self):
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)

        self.url = config['gitlab_url']
        self.project = config['gitlab_project']
        self.target_branch = config['target_branch']
        self.assignee = config['gitlab_assignee_id']
        self.source_branch = self.get_current_branch()

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
        data = {
            "source_branch": self.source_branch,
            "target_branch": self.target_branch,
            "title": title,
            "description": description,
            "assignee_id": self.assignee
        }

        response = requests.post(
            f"{self.url}/api/v4/projects/{self.project}/merge_requests",
            headers={"PRIVATE-TOKEN": self.get_api_key()},
            json=data
        )

        if response.status_code == 201:
            print("Merge request created successfully:", response.status_code)
        else:
            print(f"Failed to create merge request: {response.status_code}")
            print(f"Response text: {response.text}")


if __name__ == "__main__":
    Gitlab_api()
