import os
import subprocess


class Commit:
    model = None

    def __init__(self):
        self.diff_cmd = "git --no-pager diff --cached --ignore-space-change"
        self.show_committed_cmd = "git diff --cached --name-only"
        pass

    def get_diffs(self) -> str:
        try:
            result = subprocess.run(
                self.diff_cmd.split(),
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running git diff: {e}")
            return ""

    def commit_changes(self, commit_message: str):
        print(f"Committing changes with message: {commit_message}")

        os.system(f"git commit -m '{commit_message}'")

        # Print committed changes
        os.system(self.show_committed_cmd)
        print("Changes committed successfully")
