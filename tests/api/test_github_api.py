import pytest
import os
import subprocess
from unittest.mock import patch, Mock

from gai.api.github_api import Github_api

# --------------------------
# Fixtures
# --------------------------


@pytest.fixture
def mock_merge_requests():
    """
    Fixture to mock the Merge_requests class and its methods.
    """
    with patch('gai.api.github_api.Merge_requests') as mock_mr_class:
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
    with patch('gai.api.github_api.ConfigManager') as mock_cm_class:
        mock_cm_instance = Mock()
        mock_cm_class.return_value = mock_cm_instance

        mock_cm_instance.get_config.return_value = "main"
        yield mock_cm_instance


@pytest.fixture
def mock_get_app_name():
    """
    Fixture to mock the get_app_name function.
    """
    with patch('gai.api.github_api.get_app_name') as mock_get_app_name_fn:
        mock_get_app_name_fn.return_value = "test_app"
        yield mock_get_app_name_fn


@pytest.fixture
def mock_subprocess_run_success():
    """
    Fixture to mock subprocess.run for successful executions.
    """
    with patch('gai.api.github_api.subprocess.run') as mock_run:
        yield mock_run


@pytest.fixture
def mock_subprocess_run_failure():
    """
    Fixture to mock subprocess.run to raise CalledProcessError.
    """
    with patch('gai.api.github_api.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, ['git', 'command'])
        yield mock_run


@pytest.fixture
def mock_requests_post():
    """
    Fixture to mock requests.post.
    """
    with patch('gai.api.github_api.requests.post') as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_get():
    """
    Fixture to mock requests.get.
    """
    with patch('gai.api.github_api.requests.get') as mock_get:
        yield mock_get


@pytest.fixture
def mock_requests_patch():
    """
    Fixture to mock requests.patch.
    """
    with patch('gai.api.github_api.requests.patch') as mock_patch:
        yield mock_patch

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
# get_api_key Method Tests
# --------------------------


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


def test_create_pull_request_success(mock_requests_post, mock_merge_requests, mock_subprocess_run_success):
    """
    Test that create_pull_request successfully creates a pull request.
    """
    # Arrange
    github_api = Github_api()
    github_api.repo_owner = "owner"
    github_api.repo_name = "repo"
    github_api.target_branch = "main"
    github_api.get_current_branch = Mock(return_value="feature-branch")

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {'html_url': 'https://github.com/owner/repo/pull/1'}
        mock_requests_post.return_value = mock_response

        # Act
        with patch('builtins.print') as mock_print:
            github_api.create_pull_request("Title", "Body")

    # Assert
    mock_requests_post.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/pulls",
        headers={
            "Authorization": "token fake_token",
            "Accept": "application/vnd.github.v3+json"
        },
        json={
            "title": "Title",
            "head": "feature-branch",
            "base": "main",
            "body": "Body"
        }
    )
    mock_print.assert_any_call("Pull request created successfully.")
    mock_print.assert_any_call("Pull request URL: https://github.com/owner/repo/pull/1")


def test_create_pull_request_existing_pr(mock_requests_post, mock_merge_requests, mock_subprocess_run_success, mock_requests_get, mock_requests_patch):
    """
    Test that create_pull_request handles existing pull requests appropriately.
    """
    # Arrange
    github_api = Github_api()
    github_api.repo_owner = "owner"
    github_api.repo_name = "repo"
    github_api.target_branch = "main"
    github_api.get_current_branch = Mock(return_value="feature-branch")

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        # Simulate 422 response indicating existing PR
        mock_response_post = Mock()
        mock_response_post.status_code = 422
        mock_response_post.json.return_value = {
            'errors': [{'message': 'A pull request already exists'}]
        }
        mock_requests_post.return_value = mock_response_post

        # Simulate existing PR info
        mock_response_get = Mock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = [{
            'number': 1,
            'html_url': 'https://github.com/owner/repo/pull/1'
        }]
        mock_requests_get.return_value = mock_response_get

        # Simulate successful patch
        mock_response_patch = Mock()
        mock_response_patch.status_code = 200
        mock_requests_patch.return_value = mock_response_patch

        # Act
        with patch('builtins.print') as mock_print:
            github_api.create_pull_request("Title", "Updated Body")

    # Assert
    mock_requests_post.assert_called_once()
    mock_requests_get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/pulls",
        headers={
            "Authorization": "token fake_token",
            "Accept": "application/vnd.github.v3+json"
        },
        params={
            "head": "owner:feature-branch",
            "state": "open"
        }
    )
    mock_requests_patch.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/pulls/1",
        headers={
            "Authorization": "token fake_token",
            "Accept": "application/vnd.github.v3+json"
        },
        json={"title": "Title", "body": "Updated Body"}
    )
    mock_print.assert_any_call("A pull request already exists: https://github.com/owner/repo/pull/1")
    mock_print.assert_any_call("Pull request updated successfully.")


def test_create_pull_request_existing_pr_not_found(mock_requests_post, mock_merge_requests, mock_subprocess_run_success, mock_requests_get):
    """
    Test that create_pull_request handles existing PR not found scenario.
    """
    # Arrange
    github_api = Github_api()
    github_api.repo_owner = "owner"
    github_api.repo_name = "repo"
    github_api.target_branch = "main"
    github_api.get_current_branch = Mock(return_value="feature-branch")

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        # Simulate 422 response indicating existing PR
        mock_response_post = Mock()
        mock_response_post.status_code = 422
        mock_response_post.json.return_value = {
            'errors': [{'message': 'A pull request already exists'}]
        }
        mock_requests_post.return_value = mock_response_post

        # Simulate no existing PRs
        mock_response_get = Mock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = []
        mock_requests_get.return_value = mock_response_get

        # Act
        with patch('builtins.print') as mock_print:
            github_api.create_pull_request("Title", "Body")

    # Assert
    mock_requests_post.assert_called_once()
    mock_requests_get.assert_called_once()
    mock_print.assert_any_call("Could not find the existing pull request")


def test_create_pull_request_failure(mock_requests_post, mock_subprocess_run_success, mock_config_manager, mock_merge_requests):
    """
    Test that create_pull_request handles general failures.
    """

    github_api = Github_api()

    mock_subprocess_run_success.return_value = mock_subprocess_run_output("feature-branch\n")
    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        # Simulate failed response
        mock_response_post = Mock()
        mock_response_post.status_code = 400
        mock_response_post.json.return_value = {"message": "Bad Request"}
        mock_requests_post.return_value = mock_response_post

        # Act
        with patch('builtins.print') as mock_print:
            github_api.create_pull_request("Title", "Body")

    # Assert
    mock_requests_post.assert_called_once()

    mock_print.assert_any_call("Failed to create pull request: 400")
    mock_print.assert_any_call("Error message: {'message': 'Bad Request'}")

# --------------------------
# get_existing_pr_info Method Tests
# --------------------------


def test_get_existing_pr_info_success(mock_requests_get, mock_merge_requests, mock_config_manager):
    """
    Test that get_existing_pr_info returns existing PR info when available.
    """
    # Arrange
    github_api = Github_api()

    github_api.repo_owner = "owner"
    github_api.repo_name = "repo"
    github_api.get_current_branch = Mock(return_value="feature-branch")

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{
            'number': 1,
            'html_url': 'https://github.com/owner/repo/pull/1',
        }]
        mock_requests_get.return_value = mock_response

        # Act
        pr_info = github_api.get_existing_pr_info("https://api.github.com/repos/owner/repo/pulls")

    # Assert
    mock_requests_get.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/pulls",
        headers={
            "Authorization": "token fake_token",
            "Accept": "application/vnd.github.v3+json"
        },
        params={
            "head": "owner:feature-branch",
            "state": "open"
        }
    )
    assert pr_info == {
        'number': 1,
        'html_url': 'https://github.com/owner/repo/pull/1'
    }


def test_get_existing_pr_info_no_pr(mock_requests_get, mock_merge_requests):
    """
    Test that get_existing_pr_info returns None when no PRs are found.
    """
    # Arrange
    github_api = Github_api()
    github_api.repo_owner = "owner"
    github_api.repo_name = "repo"

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        # Act
        pr_info = github_api.get_existing_pr_info("https://api.github.com/repos/owner/repo/pulls")

    # Assert
    assert pr_info is None


def test_get_existing_pr_info_failure(mock_requests_get, mock_merge_requests):
    """
    Test that get_existing_pr_info returns None on failure.
    """
    # Arrange
    github_api = Github_api()
    github_api.repo_owner = "owner"
    github_api.repo_name = "repo"

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_requests_get.return_value = mock_response

        # Act
        pr_info = github_api.get_existing_pr_info("https://api.github.com/repos/owner/repo/pulls")

    # Assert
    assert pr_info is None

# --------------------------
# update_pull_request Method Tests
# --------------------------


def test_update_pull_request_success(mock_requests_patch, mock_merge_requests):
    """
    Test that update_pull_request successfully updates the pull request.
    """
    # Arrange
    github_api = Github_api()
    github_api.repo_owner = "owner"
    github_api.repo_name = "repo"

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests_patch.return_value = mock_response

        # Act
        with patch('builtins.print') as mock_print:
            github_api.update_pull_request("https://api.github.com/repos/owner/repo/pulls/1",
                                           title="Updated Title", body="Updated Body")

    # Assert
    mock_requests_patch.assert_called_once_with(
        "https://api.github.com/repos/owner/repo/pulls/1",
        headers={
            "Authorization": "token fake_token",
            "Accept": "application/vnd.github.v3+json"
        },
        json={
            "title": "Updated Title",
            "body": "Updated Body"
        }
    )
    mock_print.assert_any_call("Pull request updated successfully.")


def test_update_pull_request_failure(mock_requests_patch, mock_merge_requests):
    """
    Test that update_pull_request handles failures appropriately.
    """
    # Arrange
    github_api = Github_api()
    github_api.repo_owner = "owner"
    github_api.repo_name = "repo"

    with patch.dict(os.environ, {"GITHUB_TOKEN": "fake_token"}):
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"message": "Bad Request"}
        mock_requests_patch.return_value = mock_response

        # Act
        with patch('builtins.print') as mock_print:
            github_api.update_pull_request(
                "https://api.github.com/repos/owner/repo/pulls/1", title="Title", body="Body")

    # Assert
    mock_requests_patch.assert_called_once()
    mock_print.assert_any_call("Failed to update pull request: 400")
    mock_print.assert_any_call("Error message: {'message': 'Bad Request'}")

# --------------------------
# get_api_key Integration Tests
# --------------------------


def test_create_pull_request_without_api_key(mock_requests_post, mock_subprocess_run_success, mock_merge_requests, mock_config_manager):
    """
    Test that create_pull_request raises ValueError when GITHUB_TOKEN is not set.
    """
    # Arrange
    github_api = Github_api()

    github_api.get_current_branch = Mock(return_value="feature-branch")

    with patch.dict(os.environ, {}, clear=True):
        # Act & Assert
        with pytest.raises(ValueError, match="GITHUB_TOKEN is not set. Please set it in your environment variables."):
            github_api.create_pull_request("Title", "Body")

# --------------------------
# get_existing_pr_info Integration Tests
# --------------------------


def test_get_existing_pr_info_no_api_key(mock_requests_get):
    """
    Test that get_existing_pr_info raises ValueError when GITHUB_TOKEN is not set.
    """
    # Arrange
    github_api = Github_api()

    with patch.dict(os.environ, {}, clear=True):
        # Act & Assert
        with pytest.raises(ValueError, match="GITHUB_TOKEN is not set. Please set it in your environment variables."):
            github_api.get_existing_pr_info("https://api.github.com/repos/owner/repo/pulls")

# --------------------------
# update_pull_request Integration Tests
# --------------------------


def test_update_pull_request_no_api_key(mock_requests_patch):
    """
    Test that update_pull_request raises ValueError when GITHUB_TOKEN is not set.
    """
    # Arrange
    github_api = Github_api()

    # Act & Assert
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="GITHUB_TOKEN is not set. Please set it in your environment variables."):
            github_api.update_pull_request(
                "https://api.github.com/repos/owner/repo/pulls/1",
                "Title",
                "Body")
