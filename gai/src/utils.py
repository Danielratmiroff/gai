from typing import Dict, List
from colorama import Fore, Style
from importlib.metadata import version, PackageNotFoundError

import subprocess


def attr_is_defined(args, attr: str) -> bool:
    """
    Check if the specified attribute is defined in the given object.
    """
    return hasattr(args, attr) and getattr(args, attr) is not None


def get_attr_or_default(args, attr: str, default) -> any:
    """
    Get the value of the specified attribute from the object, or return a default value.
    """
    value = getattr(args, attr, default)
    return value if value is not None else default


def get_current_branch() -> str:
    """
    Retrieve the name of the current Git branch.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()


def push_changes(remote_repo: str) -> None:
    """
    Push changes to the specified remote repository.
    """
    subprocess.run(["git", "push", remote_repo])


def get_package_version(package_name: str) -> str:
    """
    Get the version of the specified package.
    """
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "Package not found"


def print_tokens(system_prompt, user_message, max_tokens):
    """
    Print the number of tokens in the system prompt and user message.
    """
    print("\n" + "="*40)
    print(f"{Fore.CYAN}System tokens: {len(system_prompt)}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}User tokens: {len(user_message)}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Max tokens: {max_tokens} | Total tokens: {
        len(user_message) + len(system_prompt)}{Style.RESET_ALL}")
    print("="*40 + "\n")


def create_user_message(user_message: str) -> Dict[str, str]:
    """
    Create a user message from the given string.
    """
    return {"role": "user", "content": user_message}


def create_system_message(system_message: str) -> Dict[str, str]:
    """
    Create a system message from the given string.
    """
    return {"role": "system", "content": system_message}
