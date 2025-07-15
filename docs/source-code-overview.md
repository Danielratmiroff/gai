# Gai Tool Source Code Documentation

This document provides an overview of the folder structure and architecture of the `gai_tool` application.

## Entry Point: `gai_tool/main.py`

The `main.py` file is the main entry point for the `gai-tool` command-line application. It is responsible for parsing command-line arguments, initializing the necessary components, and orchestrating the overall workflow.

### Functionality

The `Main` class within `main.py` orchestrates the application's functionality:

- **Argument Parsing**: The `parse_arguments` method uses `argparse` to define and parse command-line arguments, including subcommands for different operations (`init`, `merge`, `commit`).
- **Configuration Management**: It initializes the `ConfigManager` to load local (`.gai.yaml`) or global configurations.
- **AI Client Initialization**: The `init_ai_client` method dynamically selects and configures the appropriate AI client (e.g., `HuggingClient`, `GroqClient`, `GeminiClient`, `OllamaClient`) based on the user's configuration.
- **Command Execution**: Based on the parsed command, it calls the corresponding method:
  - `do_commit()`: Handles the logic for generating AI-assisted commit messages.
  - `do_merge_request()`: Manages the creation of AI-assisted merge/pull requests on platforms like GitHub or GitLab.
  - `ConfigManager.init_local_config()`: Handles the `init` command to create a local configuration file.

### Key Workflows

1.  **Commit Message Generation (`gai commit`)**:

    - Stages all changes if the `--all` flag is used.
    - Retrieves the `git diff` of staged changes.
    - Uses the selected AI client and a system prompt from `prompts.py` to generate commit message suggestions.
    - Presents the suggestions to the user for selection using `DisplayChoices`.
    - Extracts a ticket identifier from the current branch name to prepend to the commit message.
    - Commits the changes with the user-selected message.

2.  **Merge Request Generation (`gai merge`)**:
    - Optionally pushes changes to the remote repository.
    - Fetches the list of commits between the current branch and the target branch.
    - Uses the AI client to generate a merge request title and a detailed description based on the commits.
    - Presents title suggestions to the user.
    - Detects the remote platform (GitHub/GitLab) and uses the corresponding API client (`Github_api` or `Gitlab_api`) to create the merge/pull request.

## Core Logic: `gai_tool/src/`

The `gai_tool/src` directory contains the core logic for the Gai tool. The architecture is designed to be modular, with each file responsible for a specific set of functionalities.

### Directory Structure

```
gai_tool/src/
├── __init__.py
├── commits.py
├── display_choices.py
├── merge_requests.py
├── myconfig.py
├── prompts.py
└── utils.py
```

### `__init__.py`

This file serves as the entry point for the `gai_tool.src` package. It imports the main classes and functions from the other modules, making them accessible for other parts of the application.

### `commits.py`

This module handles all Git-related operations, such as:

- **`Commits` class:**
  - `get_diffs()`: Retrieves staged changes from the Git repository.
  - `commit_changes()`: Commits staged changes with a given message.
  - `stage_changes()`: Stages all changes in the repository.
  - `format_commits()`: Formats a list of commits for display.
  - `get_commits()`: Retrieves the commit history between two branches.

### `display_choices.py`

This module is responsible for the user interface and interaction.

- **`DisplayChoices` class:**
  - `parse_response()`: Parses the AI's response into a list of choices.
  - `display_choices()`: Displays a list of options for the user to select from.
  - `render_choices_with_try_again()`: Manages the interaction loop with the user, allowing them to retry or provide suggestions.

### `merge_requests.py`

This module handles interactions with remote Git repositories (e.g., GitHub, GitLab).

- **`Merge_requests` class:**
  - `get_repo_owner_from_remote_url()`: Extracts the repository owner from the remote URL.
  - `get_repo_from_remote_url()`: Extracts the repository name from the remote URL.
  - `get_remote_platform()`: Determines the Git platform (GitHub or GitLab) from the remote URL.

### `myconfig.py`

This module manages the application's configuration.

- **`ConfigManager` class:**
  - Loads and saves configuration from a local `.gai.yaml` file or a global configuration file.
  - Provides default configurations for the application.
  - Manages different AI models for providers like Groq, Hugging Face, Ollama, and Gemini.

### `prompts.py`

This module contains all the system prompts used to guide the AI's behavior.

- **`Prompts` class:**
  - `build_commit_message_system_prompt()`: Generates a system prompt for creating Git commit messages.
  - `build_merge_title_system_prompt()`: Generates a system prompt for creating merge request titles.
  - `build_merge_description_system_prompt()`: Generates a system prompt for creating merge request descriptions.
  - `build_ticket_identifier_prompt()`: Generates a system prompt for identifying ticket numbers in branch names.

### `utils.py`

This module provides a collection of utility functions used throughout the application.

- **Helper functions:**
  - `get_current_branch()`: Retrieves the current Git branch name.
  - `push_changes()`: Pushes local changes to a remote repository.
  - `get_package_version()`: Gets the version of the application package.
  - `create_user_message()` and `create_system_message()`: Formats messages for the AI client.
  - `get_ticket_identifier()`: Extracts a ticket identifier from a branch name using the AI.
