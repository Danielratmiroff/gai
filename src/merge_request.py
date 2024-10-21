import subprocess
from typing import Dict


class Merge_requests():
    def __init__(
        self,
        remote_name: str = "origin"
    ):
        self.remote_name = remote_name

    def get_repo_owner_from_remote_url(self) -> str:
        remote_url = self.get_remote_url()
        try:
            return remote_url.split(":")[1].split("/")[0]
        except IndexError:
            return "Error: Unable to get repo owner."

    def get_repo_from_remote_url(self) -> str:
        remote_url = self.get_remote_url()

        try:
            return remote_url.split(":")[1].split("/")[1].split(".")[0]
        except IndexError:
            return "Error: Unable to get repo owner."

    def get_remote_url(self, remote_name: str) -> str:
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", self.remote_name],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()

        except subprocess.CalledProcessError:
            return "Error: Unable to get remote URL. Make sure you're in a git repository."

    def get_remote_platform(self) -> str:
        remote_url = self.get_remote_url()

        print(f"remote url: {remote_url}")
        if "github" in remote_url:
            return "github"
        elif "gitlab" in remote_url:
            return "gitlab"
        else:
            return "Error: Unable to determine platform from remote URL. Only github and gitlab are supported."

    def format_commits(self, result: str) -> str:
        commits = result.split('\n')
        formatted_commits = [f"- {commit}" for commit in commits]
        return "Changes:\n" + "\n".join(formatted_commits)

    def get_commits(self, target_branch: str, source_branch: str) -> str:
        try:
            print("Fetching latest commits from remote...")
            subprocess.run(["git", "fetch", "origin"],
                           check=True, capture_output=True)

            result = subprocess.run(
                ["git", "log", "--oneline",
                    f"origin/{target_branch}..{source_branch}"],
                capture_output=True,
                text=True,
                check=True
            )

            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, result.args, result.stdout, result.stderr)

            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            return f"Error fetching commits: {e}"
