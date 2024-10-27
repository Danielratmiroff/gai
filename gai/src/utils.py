
import subprocess


class Utils:
    def get_current_branch(self) -> str:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()

    def push_changes(self, remote_repo: str):
        subprocess.run(["git", "push", remote_repo])
