import tomllib
from typing import List
from pathlib import Path
import yaml
from dataclasses import dataclass


@dataclass
class Models:
    model_name: str
    max_tokens: int


GROQ_MODELS: List[Models] = [
    Models(model_name="llama-3.3-70b-versatile", max_tokens=8000)
]


HUGGING_FACE_MODELS: List[Models] = [
    Models(model_name="Qwen/Qwen3-8B", max_tokens=32760),
]

OLLAMA_MODELS: List[Models] = [
    Models(model_name="deepseek-r1:1.5b", max_tokens=8000),
    Models(model_name="deepseek-r1:7b", max_tokens=8000),
    Models(model_name="deepseek-r1:8b", max_tokens=8000),
    Models(model_name="deepseek-r1:14b", max_tokens=8000),
    Models(model_name="phi4", max_tokens=8000),
]

GEMINI_MODELS: List[Models] = [
    Models(model_name="gemini-2.0-flash", max_tokens=8000)
]


DEFAULT_CONFIG = {
    'interface': 'huggingface',
    'temperature': 0.7,
    'target_branch': 'master',
    'assignee_id': 10437754,
}


DEFAULT_RULES = """
# Gai Rules

## Commit Messages 

- Keep the commit message summary under 72 characters.
- Use the imperative mood (e.g., "Fix issue where...", "Add feature to...", "Update dependency for...").
- Focus on the "what" and "why," not the "how."

## Pull Request Titles

- Keep the pull request title concise, under 72 characters.
- Use the imperative mood (e.g., "Add user authentication system", "Fix data processing bug").
- Summarize the essence of the combined changes in clear and concise language.

## Merge Descriptions

- Be very concise and to the point.
- Summarize the changes in bullet points.
- Focus on the overall purpose and impact of the merge.
"""

CONFIG_FILE = "config.yaml"
RULES_FILE = "gai-rules.md"
CONFIG_FOLDER = ".gai"


class ConfigManager:
    """Manage configuration for the *gai* tool.
      Precedence order: local > home > default."""

    def __init__(
        self,
        app_name: str,
        app_author: str | None = None,
        config_filename: str = CONFIG_FILE,
    ) -> None:

        # Project-level folder (./.gai)
        self.tool_folder = Path.cwd() / CONFIG_FOLDER
        self.local_config_path = self.tool_folder / config_filename

        # Home-level folder (~/.gai)
        self.home_tool_folder = Path.home() / CONFIG_FOLDER
        self.home_config_path = self.home_tool_folder / config_filename

        self.config = self.load_config()

    # ------------------------------------------------------------------
    # Configuration loading helpers
    # ------------------------------------------------------------------
    def _read_yaml(self, path: Path) -> dict:
        if not path.exists():
            return {}
        with path.open("r") as f:
            data = yaml.safe_load(f)
            return data or {}

    def load_config(self) -> dict:
        """Load the configuration following the precedence rules.
        Local > Home > Default. No merging."""

        local_config = self._read_yaml(self.local_config_path)
        if local_config:
            return local_config

        home_config = self._read_yaml(self.home_config_path)
        if home_config:
            return home_config

        return DEFAULT_CONFIG.copy()

    def create_default_config(self) -> None:
        """Create a default * project * configuration file."""
        self.tool_folder.mkdir(parents=True, exist_ok=True)

        with self.local_config_path.open("w") as f:
            yaml.dump(DEFAULT_CONFIG, f)
        print(f"Created default config at {self.local_config_path}")

    def save_config(self) -> None:
        """Persist the current configuration to the * project * ``.gai`` folder."""

        # Ensure folder exists
        self.tool_folder.mkdir(parents=True, exist_ok=True)

        with self.local_config_path.open("w") as f:
            yaml.dump(self.config, f)
        print(f"Saved config to {self.local_config_path}")

    def update_config(self, key, value):
        self.config[key] = value
        self.save_config()

    def get_config(self, key, default=None):
        return self.config.get(key, default)

    def init_local_config(self):
        """Initialize a local configuration file in the current directory."""
        if self.local_config_path.exists():
            print(f"Local config already exists at {self.local_config_path}")
            return False

        self.tool_folder.mkdir(exist_ok=True)

        with self.local_config_path.open('w') as f:
            yaml.dump(self.config, f)
        print(f"Created local config at {self.local_config_path}")

        # Create rules file
        rules_path = self.tool_folder / RULES_FILE
        if not rules_path.exists():
            with rules_path.open('w') as f:
                f.write(DEFAULT_RULES)
            print(f"Created rules file at {rules_path}")

        return True


def get_app_name():
    try:
        with open('pyproject.toml', 'rb') as f:
            pyproject = tomllib.load(f)
        return pyproject['project']['name']
    except (FileNotFoundError, KeyError):
        return "gai-tool"


if __name__ == "__main__":
    config_manager = ConfigManager(get_app_name())
    target_branch = config_manager.get_config('target_branch')
    print(f"Target branch: {target_branch}")
