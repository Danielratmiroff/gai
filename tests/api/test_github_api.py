import pytest
import os
import subprocess
from unittest.mock import MagicMock, patch, Mock

from gai_tool.api.github_api import Github_api

# --------------------------
# Fixtures
# --------------------------


@pytest.fixture
def mock_merge_requests():
    """
    Fixture to mock the Merge_requests class and its methods.
    """
    with patch('gai_tool.api.github_api.Merge_requests') as mock_mr_class:
        mock_mr_instance = Mock()
        mock_mr_class.return_value.get_instance.return_value = mock_mr_instance

        mock_mr_instance.get_repo_owner_from_remote_url.return_value = "owner"
        mock_mr_instance.get_repo_from_remote_url.return_value = "repo"
        mock_mr_instance.get_current_branch.return_value = "feature-branch"
        yield mock_mr_instance


@pytest.fixture
def mock_config_manager():
    """
    Fixture to mock the ConfigManager class and its methods.
    """
    with patch('gai_tool.api.github_api.ConfigManager') as mock_cm_class:
        mock_cm_instance = Mock()
        mock_cm_class.return_value = mock_cm_instance

        mock_cm_instance.get_config.return_value = "main"
        yield mock_cm_instance


@pytest.fixture
def mock_get_app_name():
    """
    Fixture to mock the get_app_name function.
    """
    with patch('gai_tool.api.github_api.get_app_name') as mock_get_app_name_fn:
        mock_get_app_name_fn.return_value = "test_app"
        yield mock_get_app_name_fn


@pytest.fixture
def mock_subprocess_run_success():
    """
    Fixture to mock subprocess.run for successful executions.
    """
    with patch('gai_tool.api.github_api.subprocess.run') as mock_run:
        yield mock_run


@pytest.fixture
def mock_subprocess_run_failure():
    """
    Fixture to mock subprocess.run to raise CalledProcessError.
    """
    with patch('gai_tool.api.github_api.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ['git', 'command'])
        yield mock_run


@pytest.fixture
def mock_github():
    """
    Fixture to mock the Github class from PyGithub.
    """
    with patch('gai_tool.api.github_api.Github') as mock_github_class:
        yield mock_github_class


@pytest.fixture
def mock_repo():
    """
    Fixture to mock a GitHub repository object.
    """
    mock_repo = Mock()
    yield mock_repo


@pytest.fixture
def mock_pull_request():
    """
    Fixture to mock a GitHub pull request object.
    """
    mock_pr = Mock()
    mock_pr.html_url = "https://github.com/owner/repo/pull/1"
    mock_pr.number = 1
    yield mock_pr


# --------------------------
# Helper Functions
# --------------------------


def mock_subprocess_run_output(output, returncode=0):
    """
    Helper function to create a mock subprocess.run return value with specified output and returncode.
    """
    mock = Mock()
    mock.stdout = output
    mock.returncode = returncode
    return mock

# --------------------------
# Initialization Tests
# --------------------------


def test_github_api_initialization(mock_merge_requests, mock_config_manager, mock_get_app_name):
    """
    Test the initialization of Github_api class.
    """
    # Act
    github_api = Github_api()

    # Assert
    mock_config_manager.get_config.assert_called_once_with('target_branch')

    assert github_api.repo_owner == "owner"
    assert github_api.repo_name == "repo"
    assert github_api.target_branch == "main"
    assert github_api._github is None

# --------------------------
# load_config Method Tests
# --------------------------


def test_load_config_success(mock_merge_requests, mock_config_manager, mock_get_app_name):
    """
    Test that load_config successfully loads configuration.
    """
    # Arrange
    mock_config_manager.get_config.return_value = "develop"

    # Act
    github_api = Github_api()

    # Assert
    assert github_api.target_branch == "develop"

# --------------------------
# GitHub Property Tests
# --------------------------


def test_github_property_lazy_initialization(mock_github, mock_merge_requests, mock_config_manager):
    """
    Test that the github property initializes the GitHub client lazily.
    """
    # Arrange
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        github_api = Github_api()

        # Act
        github_client = github_api.github

        # Assert
        mock_github.assert_called_once_with("fake_token")
        assert github_api._github is not None


def test_repo_property(mock_github, mock_repo, mock_merge_requests, mock_config_manager):
    """
    Test that the repo property returns the correct repository object.
    """
    # Arrange
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        mock_github_instance = mock_github.return_value
        mock_github_instance.get_repo.return_value = mock_repo
        github_api = Github_api()

        # Act
        repo = github_api.repo

        # Assert
        mock_github_instance.get_repo.assert_called_once_with("owner/repo")
        assert repo == mock_repo

# --------------------------
# get_current_branch Method Tests
# --------------------------


def test_get_current_branch_success(mock_subprocess_run_success, mock_merge_requests, mock_config_manager):
    """
    Test that get_current_branch returns the current branch name successfully.
    """
    # Arrange
    mock_subprocess_run_success.return_value = mock_subprocess_run_output("feature-branch\n")

    github_api = Github_api()

    # Act
    branch = github_api.get_current_branch()

    # Assert
    assert branch == "feature-branch"
    mock_subprocess_run_success.assert_called_with(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True
    )


def test_get_current_branch_failure(mock_subprocess_run_failure, mock_merge_requests, mock_config_manager):
    """
    Test that get_current_branch propagates the CalledProcessError when subprocess fails.
    """
    github_api = Github_api()

    # Act & Assert
    with pytest.raises(subprocess.CalledProcessError):
        github_api.get_current_branch()

# --------------------------
# create_pull_request Method Tests
# --------------------------


def test_create_pull_request_success_new_pr(mock_github, mock_repo, mock_pull_request, mock_merge_requests, mock_config_manager):
    """
    Test that create_pull_request successfully creates a new pull request.
    """
    # Arrange
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        github_api = Github_api()
        github_api.get_current_branch = Mock(return_value="feature-branch")
        github_api.get_existing_pr = Mock(return_value=None)

        mock_github_instance = mock_github.return_value
        mock_github_instance.get_repo.return_value = mock_repo
        mock_repo.create_pull.return_value = mock_pull_request

        # Act
        with patch('builtins.print') as mock_print:
            github_api.create_pull_request("Test Title", "Test Body")

        # Assert
        mock_repo.create_pull.assert_called_once_with(
            title="Test Title",
            body="Test Body",
            head="feature-branch",
            base="main"
        )
        mock_print.assert_any_call("Pull request created successfully.")
        mock_print.assert_any_call("Pull request URL: https://github.com/owner/repo/pull/1")


def test_create_pull_request_existing_pr(mock_github, mock_repo, mock_pull_request, mock_merge_requests, mock_config_manager):
    """
    Test that create_pull_request updates an existing pull request.
    """
    # Arrange
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        github_api = Github_api()
        github_api.get_current_branch = Mock(return_value="feature-branch")
        github_api.get_existing_pr = Mock(return_value=mock_pull_request)
        github_api.update_pull_request = Mock()

        mock_github_instance = mock_github.return_value
        mock_github_instance.get_repo.return_value = mock_repo

        # Act
        with patch('builtins.print') as mock_print:
            github_api.create_pull_request("Updated Title", "Updated Body")

        # Assert
        github_api.update_pull_request.assert_called_once_with(
            mock_pull_request,
            title="Updated Title",
            body="Updated Body"
        )
        mock_print.assert_any_call("A pull request already exists: https://github.com/owner/repo/pull/1")


def test_create_pull_request_github_exception(mock_github, mock_repo, mock_merge_requests, mock_config_manager):
    """
    Test that create_pull_request handles GithubException appropriately.
    """
    # Arrange
    from github import GithubException

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        github_api = Github_api()
        github_api.get_current_branch = Mock(return_value="feature-branch")
        github_api.get_existing_pr = Mock(side_effect=GithubException(400, {"message": "Bad Request"}))

        mock_github_instance = mock_github.return_value
        mock_github_instance.get_repo.return_value = mock_repo

        # Act
        with patch('builtins.print') as mock_print:
            github_api.create_pull_request("Title", "Body")

        # Assert
        mock_print.assert_any_call("Failed to create pull request: 400")
        mock_print.assert_any_call("Error message: {'message': 'Bad Request'}")


def test_create_pull_request_general_exception(mock_github, mock_repo, mock_merge_requests, mock_config_manager):
    """
    Test that create_pull_request handles general exceptions appropriately.
    """
    # Arrange
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        github_api = Github_api()
        github_api.get_current_branch = Mock(return_value="feature-branch")
        github_api.get_existing_pr = Mock(side_effect=Exception("Unexpected error"))

        mock_github_instance = mock_github.return_value
        mock_github_instance.get_repo.return_value = mock_repo

        # Act
        with patch('builtins.print') as mock_print:
            github_api.create_pull_request("Title", "Body")

        # Assert
        mock_print.assert_any_call("Unexpected error: Unexpected error")

# --------------------------
# get_existing_pr Method Tests
# --------------------------


def test_get_existing_pr_success(mock_github, mock_repo, mock_pull_request, mock_merge_requests, mock_config_manager):
    """
    Test that get_existing_pr returns existing PR when available.
    """
    # Arrange
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        github_api = Github_api()
        github_api.get_current_branch = Mock(return_value="feature-branch")

        mock_github_instance = mock_github.return_value
        mock_github_instance.get_repo.return_value = mock_repo
        mock_repo.get_pulls.return_value = [mock_pull_request]

        # Act
        result = github_api.get_existing_pr()

        # Assert
        mock_repo.get_pulls.assert_called_once_with(
            state='open',
            head='owner:feature-branch'
        )
        assert result == mock_pull_request


def test_get_existing_pr_no_pr(mock_github, mock_repo, mock_merge_requests, mock_config_manager):
    """
    Test that get_existing_pr returns None when no PRs are found.
    """
    # Arrange
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        github_api = Github_api()
        github_api.get_current_branch = Mock(return_value="feature-branch")

        mock_github_instance = mock_github.return_value
        mock_github_instance.get_repo.return_value = mock_repo
        mock_repo.get_pulls.return_value = []

        # Act
        result = github_api.get_existing_pr()

        # Assert
        assert result is None


def test_get_existing_pr_github_exception(mock_github, mock_repo, mock_merge_requests, mock_config_manager):
    """
    Test that get_existing_pr handles GithubException appropriately.
    """
    # Arrange
    from github import GithubException

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        github_api = Github_api()
        github_api.get_current_branch = Mock(return_value="feature-branch")

        mock_github_instance = mock_github.return_value
        mock_github_instance.get_repo.return_value = mock_repo
        mock_repo.get_pulls.side_effect = GithubException(500, {"message": "Server Error"})

        # Act
        with patch('builtins.print') as mock_print:
            result = github_api.get_existing_pr()

        # Assert
        mock_print.assert_any_call("Error fetching pull requests: 500")
        mock_print.assert_any_call("Error message: {'message': 'Server Error'}")
        assert result is None

# --------------------------
# update_pull_request Method Tests
# --------------------------


def test_update_pull_request_success(mock_pull_request, mock_merge_requests, mock_config_manager):
    """
    Test that update_pull_request successfully updates the pull request.
    """
    # Arrange
    github_api = Github_api()

    # Act
    with patch('builtins.print') as mock_print:
        github_api.update_pull_request(mock_pull_request, "Updated Title", "Updated Body")

    # Assert
    mock_pull_request.edit.assert_called_once_with(title="Updated Title", body="Updated Body")
    mock_print.assert_any_call("Pull request updated successfully.")


def test_update_pull_request_github_exception(mock_pull_request, mock_merge_requests, mock_config_manager):
    """
    Test that update_pull_request handles GithubException appropriately.
    """
    # Arrange
    from github import GithubException

    github_api = Github_api()
    mock_pull_request.edit.side_effect = GithubException(400, {"message": "Bad Request"})

    # Act
    with patch('builtins.print') as mock_print:
        github_api.update_pull_request(mock_pull_request, "Title", "Body")

    # Assert
    mock_print.assert_any_call("Failed to update pull request: 400")
    mock_print.assert_any_call("Error message: {'message': 'Bad Request'}")


def test_update_pull_request_general_exception(mock_pull_request, mock_merge_requests, mock_config_manager):
    """
    Test that update_pull_request handles general exceptions appropriately.
    """
    # Arrange
    github_api = Github_api()
    mock_pull_request.edit.side_effect = Exception("Unexpected error")

    # Act
    with patch('builtins.print') as mock_print:
        github_api.update_pull_request(mock_pull_request, "Title", "Body")

    # Assert
    mock_print.assert_any_call("Unexpected error: Unexpected error")

# --------------------------
# get_api_key Integration Tests
# --------------------------


def test_create_pull_request_without_api_key(mock_merge_requests, mock_config_manager):
    """
    Test that create_pull_request prints error when GITHUB_TOKEN is not set.
    """
    # Arrange
    github_api = Github_api()
    github_api.get_current_branch = Mock(return_value="feature-branch")

    with patch.dict(os.environ, {}, clear=True):
        # Act & Assert
        with patch('builtins.print') as mock_print:
            github_api.create_pull_request("Title", "Body")

        # Check that the ValueError message is printed as an unexpected error
        mock_print.assert_any_call(
            "Unexpected error: GITHUB_TOKEN is not set. Please set it in your environment variables.")


def test_get_existing_pr_no_api_key(mock_merge_requests, mock_config_manager):
    """
    Test that get_existing_pr raises ValueError when GITHUB_TOKEN is not set.
    """
    # Arrange
    github_api = Github_api()

    with patch.dict(os.environ, {}, clear=True):
        # Act & Assert
        with pytest.raises(ValueError, match="GITHUB_TOKEN is not set. Please set it in your environment variables."):
            github_api.get_existing_pr()


def test_github_property_no_api_key(mock_merge_requests, mock_config_manager):
    """
    Test that accessing github property raises ValueError when GITHUB_TOKEN is not set.
    """
    # Arrange
    github_api = Github_api()

    with patch.dict(os.environ, {}, clear=True):
        # Act & Assert
        with pytest.raises(ValueError, match="GITHUB_TOKEN is not set. Please set it in your environment variables."):
            _ = github_api.github
