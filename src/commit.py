import os


class Commit:
    model = None

    def __init__(self):
        self.cmd = "git --no-pager diff --cached --ignore-space-change"
        pass

    def read_diff_file(self, diff_file_path):
        with open(diff_file_path, "r") as file:
            return file.read()

    def clean_file(self, diff_file_path):
        if os.path.exists(diff_file_path):
            os.remove(diff_file_path)

    def get_diffs(self) -> str:
        # Stage all changes to be able to get the diff
        os.system("git add .")

        # We store the diff in a file to avoid printing it to the console
        diff_file_path = os.path.join(os.getcwd(), "diff.txt")
        os.system(f"{self.cmd} --output={diff_file_path}")

        self_diff = self.read_diff_file(diff_file_path)

        # Clean up the file
        self.clean_file(diff_file_path)

        return self_diff
