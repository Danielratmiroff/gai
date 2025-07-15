# Testing Guidelines

This document outlines the testing practices, patterns, and architecture for the `gai-tool` project. Adhering to these guidelines ensures consistency, maintainability, and reliability of our tests.

## Testing Framework

We use **Pytest** as our primary testing framework. It provides a rich set of features, including fixtures, assertions, and a powerful plugin system.

- **Key Library:** `pytest`
- **Assertions:** Use standard Python `assert` statements. Pytest enhances them to provide detailed output on failures.

## How to Run Tests

Tests can be executed using the Poetry script defined in `pyproject.toml`.

```bash
poetry run test
```

This command will discover and run all tests located in the `tests/` directory. You can also pass any standard Pytest arguments to this command:

```bash
# Run tests with verbose output
poetry run test -v

# Run a specific test file
poetry run test tests/src/test_commits.py

# Run tests with coverage
poetry run test --cov=gai_tool
```

## Directory Structure

The test suite is located in the `tests/` directory. The structure of this directory mirrors the main application's source code in `gai_tool/` to make it easy to locate tests for specific modules.

```
tests/
├── api/
│   ├── test_github_api.py
│   └── test_gitlab_api.py
├── src/
│   ├── test_commits.py
│   └── test_display_choices.py
├── main.py         # Test runner script
└── test_helpers.py # Shared test utilities
```

## Writing Tests

### File and Function Naming

- **Test Files:** Must be prefixed with `test_` (e.g., `test_commits.py`).
- **Test Functions:** Must be prefixed with `test_` and should have descriptive names that indicate what they are testing, following a pattern like `test_<function>_<condition>`. For example: `test_get_commits_success` or `test_create_pull_request_github_exception`.
- **Test comments**: Must add a comment to the top of the test function to describe what it is testing.

### Test Structure (Arrange-Act-Assert)

Tests should be structured following the **Arrange-Act-Assert** pattern for clarity and readability.

```python
def test_get_commits_success(mock_subprocess_run_success, commit_instance):
    # Arrange: Set up preconditions and mock objects
    mock_log = mock_subprocess_run_output("commit1\ncommit2", 0)
    mock_subprocess_run_success.return_value = mock_log

    # Act: Call the function or method being tested
    commits = commit_instance.get_commits("origin", "main", "feature-branch")

    # Assert: Verify the outcome
    assert commits == "commit1\ncommit2"
```

### Fixtures

Fixtures are a cornerstone of our testing strategy. They provide a fixed baseline upon which tests can reliably and repeatedly execute.

- **Purpose:** Use `@pytest.fixture` to set up objects, mock dependencies, and manage state for tests.
- **Location:** Fixtures can be defined within a test file for local use or in `conftest.py` files for broader use (though we currently define them locally).
- **Examples:**
  - Providing a clean instance of a class: `commit_instance()`
  - Mocking dependencies like `subprocess.run`: `mock_subprocess_run_success()`
  - Resetting singletons to ensure test isolation: `reset_singleton()`

```python
@pytest.fixture
def commit_instance():
    """
    Fixture to provide a fresh instance of Commit for tests.
    """
    return Commits()
```

### Mocking

We use `unittest.mock` (including `patch`, `Mock`, `MagicMock`) extensively to isolate the code under test from its dependencies (e.g., external APIs, filesystem, subprocesses).

- **Mocking Subprocesses:** A common pattern is to mock `subprocess.run` to simulate different outcomes of shell commands.

  ```python
  @pytest.fixture
  def mock_subprocess_run_failure():
      """
      Fixture to mock subprocess.run to raise CalledProcessError.
      """
      with patch('gai_tool.src.commits.subprocess.run') as mock_run:
          mock_run.side_effect = subprocess.CalledProcessError(1, ['git', 'command'])
          yield mock_run
  ```

- **Mocking Classes and Methods:** Patch entire classes or specific methods to control their behavior during tests.

### Testing Exceptions

To verify that our code correctly raises exceptions under error conditions, use `pytest.raises`.

```python
def test_get_commits_fetch_failure(mock_subprocess_run_failure, commit_instance):
    with pytest.raises(subprocess.CalledProcessError):
        commit_instance.get_commits("origin", "main", "feature-branch")
```

## Testing Patterns & Best Practices

- **Test Isolation:** Tests must be independent. A crucial pattern for this in our codebase is the `reset_singleton` fixture in `tests/src/test_merge_requests.py`, which ensures that tests for our singleton `Merge_requests` class do not interfere with each other.
- **Helper Functions:** Reusable logic for setting up mocks or creating test data should be placed in helper functions. For globally shared helpers, use `tests/test_helpers.py`.
- **Clarity and Grouping:** Use comments (`# --------------------------`) to group related tests within a file (e.g., by method) to improve readability.

## Example Test

Here is an example from `tests/src/test_commits.py` that illustrates many of the concepts above:

```python
import pytest
import subprocess
from unittest.mock import patch, Mock

from gai_tool.src.commits import Commits
from tests.test_helpers import mock_subprocess_run_output

# Fixture for the class instance
@pytest.fixture
def commit_instance():
    return Commits()

# Fixture for mocking a successful subprocess call
@pytest.fixture
def mock_subprocess_run_success():
    with patch('gai_tool.src.commits.subprocess.run') as mock_run:
        yield mock_run

# Test for a successful execution path
def test_get_commits_success(mock_subprocess_run_success, commit_instance):
    # Arrange
    mock_fetch = mock_subprocess_run_output("", 0)
    mock_log = mock_subprocess_run_output("commit1\ncommit2", 0)
    mock_subprocess_run_success.side_effect = [mock_fetch, mock_log]

    # Act
    commits = commit_instance.get_commits("origin", "main", "feature-branch")

    # Assert
    assert commits == "commit1\ncommit2"
    mock_subprocess_run_success.assert_any_call(
        ["git", "fetch", "origin"],
        check=True,
        capture_output=True
    )
```
