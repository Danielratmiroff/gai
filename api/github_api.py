import os
import requests
import yaml
import subprocess


class Github_api():
    def __init__(self):
        self.load_config()

    def load_config(self):
        with open("config.yaml", "r") as file:
            config = yaml.safe_load(file)

        self.owner = config['github_owner']
        self.repo = config['github_repo']
        self.target_branch = config['target_branch']
        self.source_branch = self.get_current_branch()

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
        data = {
            "title": title,
            "head": self.source_branch,
            "base": self.target_branch,
            "body": body
        }

        response = requests.post(
            f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls",
            headers={
                "Authorization": f"token {self.get_api_key()}",
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


# TODO: remove this
if __name__ == "__main__":
    Github_api()
