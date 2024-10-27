
import subprocess


def get_attr_or_default(args, attr, default):
    value = getattr(args, attr, default)
    return value if value is not None else default


def get_current_branch(self) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def push_changes(self, remote_repo: str):
    subprocess.run(["git", "push", remote_repo])
