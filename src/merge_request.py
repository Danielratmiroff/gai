import subprocess


class Merge_requests():
    def __init__(self):
        pass

    def format_commits(self, result: str) -> str:
        commits = result.split('\n')
        formatted_commits = [f"- {commit}" for commit in commits]
        return "Changes:\n" + "\n".join(formatted_commits)

    def get_commits(self, target_branch: str) -> str:
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", f"{target_branch}..HEAD"],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                raise subprocess.CalledProcessError(
                    result.returncode, result.args, result.stdout, result.stderr)

            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            return f"Error fetching commits: {e}"
