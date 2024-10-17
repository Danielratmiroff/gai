import os


class Commit:
    model = None

    def __init__(self):
        self.diff_cmd = "git --no-pager diff --cached --ignore-space-change"
        self.show_committed_cmd = "git diff --cached --name-only"
        pass

    def read_diff_file(self, diff_file_path: str) -> str:
        with open(diff_file_path, "r") as file:
            return file.read()

    def clean_file(self, diff_file_path: str):
        if os.path.exists(diff_file_path):
            os.remove(diff_file_path)

    def get_diffs(self) -> str:
        # We store the diff in a file to avoid printing it to the console
        diff_file_path = os.path.join(os.getcwd(), "diff.txt")
        os.system(f"{self.diff_cmd} --output={diff_file_path}")

        self_diff = self.read_diff_file(diff_file_path)

        # Clean up the file
        self.clean_file(diff_file_path)

        return self_diff

    def commit_changes(self, commit_message: str):
        print(f"Committing changes with message: {commit_message}")

        os.system(f"git commit -m '{commit_message}'")

        # Print committed changes
        os.system(self.show_committed_cmd)
        print("Changes committed successfully")
