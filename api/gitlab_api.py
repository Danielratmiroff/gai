import os
import requests
import yaml
import subprocess


class Gitlab_api():
    def __init__(self):
        self.load_config()
        self.create_merge_request()

    def load_config(self):
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)

        self.url = config['gitlab_url']
        self.project = config['gitlab_project']
        self.target_branch = config['target_branch']

        self.private_token = os.environ.get("GITLAB_PRIVATE_TOKEN")
        if not self.private_token:
            raise ValueError(
                "GITLAB_PRIVATE_TOKEN environment variable is not set")

        self.source_branch = self.get_current_branch()

    def get_current_branch(self):
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        return result.stdout.strip()

    def create_merge_request(self):
        data = {
            "source_branch": self.source_branch,
            "target_branch": self.target_branch,
            "title": "My Merge Request",
            "description": "This is a dummy merge request created via API.",
        }

        # Make the request to create the merge request
        response = requests.post(
            f"{self.url}/api/v4/projects/{self.project}/merge_requests",
            headers={"PRIVATE-TOKEN": self.private_token},
            json=data
        )

        # Check the response
        if response.status_code == 201:
            print("Merge request created successfully:", response.json())
        else:
            print(f"Failed to create merge request: {response.status_code}")
            print(f"Response text: {response.text}")


if __name__ == "__main__":
    Gitlab_api()
