import subprocess
from typing import Dict


class Merge_requests:
    def __init__(self, remote_name="origin"):
        self.remote_name = remote_name

    @classmethod
    def get_instance(cls, remote_name="origin"):
        """
        Factory method to get or create singleton instance
        """
        if not hasattr(cls, '_instance'):
            cls._instance = cls(remote_name)
        return cls._instance

    @classmethod
    def initialize(cls, remote_name: str):
        """
        Initialize or reinitialize the singleton instance
        """
        cls._instance = cls(remote_name)
        return cls._instance

    def get_repo_owner_from_remote_url(self) -> str:
        remote_url = self.git_repo_url()
        try:
            return remote_url.split(":")[1].split("/")[0]
        except IndexError:
            return "Error: Unable to get repo owner."

    def get_repo_from_remote_url(self) -> str:
        remote_url = self.git_repo_url()

        try:
            return remote_url.split(":")[1].split("/")[1].split(".")[0]
        except IndexError:
            return "Error: Unable to get repo owner."

    # Extract the domain from the Git URL
    def get_remote_url(self) -> str:
        remote_url = self.git_repo_url()

        try:
            if remote_url.startswith("git@"):
                domain = remote_url.split("@")[1].split(":")[0]

            elif remote_url.startswith("https://"):
                domain = remote_url.split("//")[1].split("/")[0]

            raise ValueError(f"Unsupported Git URL format ${remote_url}")

            return domain
        except IndexError:
            return "Error: Unable to get remote URL."

    def git_repo_url(self) -> str:
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
        remote_url = self.git_repo_url()

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
            subprocess.run(["git", "fetch", self.remote_name],
                           check=True, capture_output=True)

            result = subprocess.run(
                ["git", "log", "--oneline",
                    f"{self.remote_name}/{target_branch}..{source_branch}"],
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
