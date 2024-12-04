import os
import subprocess

from colorama import Fore, Style


class Commits:
    def __init__(self):
        self.diff_cmd = "git --no-pager diff --cached --ignore-space-change"
        self.show_committed_cmd = "git diff --cached --name-only"

    def get_diffs(self) -> str:
        try:
            result = subprocess.run(
                self.diff_cmd.split(),
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running git diff: {e}")
            return ""

    def commit_changes(self, commit_message: str):
        print(f"Committing changes with message: {commit_message}")

        os.system(f"git commit -m '{commit_message}'")

        # Print committed changes
        os.system(self.show_committed_cmd)
        print("Changes committed successfully")

    def stage_changes(self):
        print(f"{Fore.GREEN}Staging all changes...{Style.RESET_ALL}")
        os.system("git add .")

    def format_commits(self, result: str) -> str:
        commits = result.split('\n')
        formatted_commits = [f"- {commit}" for commit in commits]

        return "Changes:\n" + "\n".join(formatted_commits)

    def get_commits(self, remote_repo: str, target_branch: str, source_branch: str) -> str:
        try:
            remote = remote_repo or "origin"

            print("Fetching latest commits from remote...")
            subprocess.run(["git", "fetch", remote],
                           check=True, capture_output=True)

            result = subprocess.run(
                ["git", "log", "--oneline",
                    f"{remote}/{target_branch}..{source_branch}"],
                capture_output=True,
                text=True,
                check=True
            )

            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, result.args, result.stdout, result.stderr)

            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            raise e
