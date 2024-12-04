import subprocess
from typing import Callable, Dict, List

from gai.src.prompts import Prompts
from gai.src.utils import create_system_message, create_user_message


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

    def get_ticket_identifier(self, branch_name: str, ai_client: Callable[[str, str], str]) -> str:
        prompt = Prompts().build_ticket_identifier_prompt()

        messages: List[Dict[str, str]] = [
            create_system_message(prompt),
            create_user_message(branch_name)
        ]

        response = ai_client(
            user_message=messages.copy(),
        )
        return None if response == "None" else response

    def get_repo_owner_from_remote_url(self) -> str:
        """
        Get the repository owner from the current git remote URL.
        """
        try:
            remote_url = self.git_repo_url()
            return parse_repo_owner(remote_url)
        except (ValueError, Exception) as e:
            raise ValueError("Error: Unable to get repo owner.") from e

    def get_repo_from_remote_url(self) -> str:
        """
        Get the repository name from the current git remote URL.

        Returns:
            str - The repository name or error message
        """
        try:
            remote_url = self.git_repo_url()
            return parse_repo_name(remote_url)
        except ValueError:
            return "Error: Unable to get repo owner."

    def get_remote_url(self) -> str:
        remote_url = self.git_repo_url()
        return remote_url.split("/")[0]

    def git_repo_url(self) -> str:
        """
        Gets the remote URL of the current git repository and returns it in the format "domain/owner/repo.git".

        Sample remote URL:
            git@github.com:user/repo.git or https://github.com:user/repo.git

        Returns:
            "github.com/user/repo.git"

        """
        try:
            result = subprocess.run(
                ["git", "remote", "get-url", self.remote_name],
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()

            if result.startswith("git@"):
                url = result.split("@")[1].replace(":", "/")

            elif result.startswith("https://"):
                url = result.split("//")[1]

            return url

        except subprocess.CalledProcessError:
            return "Error: Unable to get remote URL. Make sure you're in a git repository."

    def get_remote_platform(self) -> str:
        remote_url = self.git_repo_url()

        print(f"remote url: {remote_url}")
        if "github" in remote_url:
            return "github"
        elif "gitlab" in remote_url or "git." in remote_url:
            return "gitlab"
        else:
            return "Error: Unable to determine platform from remote URL. Only github and gitlab are supported."


############################################################################################################
# Helper functions
############################################################################################################


def parse_repo_owner(url: str) -> str:
    """
    Parse the repository owner from a git URL string.
    """
    if not url:
        raise ValueError("Repository URL cannot be empty")

    # Remove trailing and starting slashes
    segments = url.lstrip("/").rstrip("/").split("/")

    if len(segments) < 3:
        raise ValueError(f"Invalid repository URL format: {url}")

    owner = segments[1]
    if not owner:
        raise ValueError("Repository owner cannot be empty")

    return owner


def parse_repo_name(url: str) -> str:
    """
    Parse the repository name from a git URL string (supports both SSH and HTTPS formats).
    """
    if not url:
        raise ValueError("Repository URL cannot be empty")

    # Remove trailing slashes and spaces
    url = url.strip().rstrip('/')

    try:
        # Must have both owner and repo parts
        if '/' not in url or url.count('/') < 2:
            raise ValueError(
                f"URL must contain both owner and repository: {url}")

        # Get just the repo name (part after the last '/')
        repo_name = url.split('/')[-1].replace('.git', '')

        if not repo_name:
            raise ValueError("Repository name cannot be empty")

        return repo_name

    except IndexError:
        raise ValueError(f"Unable to extract repository name from: {url}")
