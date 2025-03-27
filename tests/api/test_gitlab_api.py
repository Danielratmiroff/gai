import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
import os
import subprocess
import requests

from gai_tool.api import Gitlab_api
from tests.test_helpers import mock_subprocess_run_output


@pytest.fixture
def mock_merge_requests():
    """
    Fixture to mock the Merge_requests class and its methods.
    """
    with patch('gai_tool.api.gitlab_api.Merge_requests') as mock_mr_class:
        mock_mr_instance = Mock()
        mock_mr_class.return_value.get_instance.return_value = mock_mr_instance

        mock_mr_instance.get_repo_owner_from_remote_url.return_value = "owner"
        mock_mr_instance.get_repo_from_remote_url.return_value = "repo"
        mock_mr_instance.get_current_branch.return_value = "feature-branch"
        mock_mr_instance.get_remote_url.return_value = "gitlab.com"
        yield mock_mr_instance


@pytest.fixture
def mock_config_manager():
    """
    Fixture to mock the ConfigManager class and its methods.
    """
    with patch('gai_tool.api.gitlab_api.ConfigManager') as mock_cm_class:
        mock_cm_instance = Mock()
        mock_cm_class.return_value = mock_cm_instance

        mock_cm_instance.get_config.side_effect = ["main", 12345]
        yield mock_cm_instance


@pytest.fixture
def mock_get_app_name():
    """
    Fixture to mock the get_app_name function.
    """
    with patch('gai_tool.api.gitlab_api.get_app_name') as mock_get_app_name_fn:
        mock_get_app_name_fn.return_value = "test_app"
        yield mock_get_app_name_fn


@pytest.fixture
def gitlab_api(mock_merge_requests):
    """
    Fixture to initialize the Gitlab_api instance with mocked Merge_requests.
    """
    return Gitlab_api()


@pytest.fixture
def mock_subprocess_run_success():
    """
    Fixture to mock subprocess.run for successful executions.
    Returns a mock that can be configured per test.
    """
    with patch('gai_tool.src.merge_requests.subprocess.run') as mock_run:
        yield mock_run


@pytest.fixture
def mock_subprocess_run_failure():
    """
    Fixture to mock subprocess.run to raise CalledProcessError.
    """
    with patch('gai_tool.src.merge_requests.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['git', 'command'])
        yield mock_run


@pytest.fixture
def mock_requests_post():
    """
    Fixture to mock requests.post.
    """
    with patch('gai_tool.api.gitlab_api.requests.post') as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_get():
    """
    Fixture to mock requests.get.
    """
    with patch('gai_tool.api.gitlab_api.requests.get') as mock_get:
        yield mock_get


@pytest.fixture
def mock_requests_put():
    """
    Fixture to mock requests.put.
    """
    with patch('gai_tool.api.gitlab_api.requests.put') as mock_put:
        yield mock_put


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


def test_load_config(gitlab_api, mock_config_manager, mock_get_app_name):
    """
    Test the load_config method to ensure configuration is loaded correctly.
    """
    # Given
    gitlab_api = Gitlab_api()

    mock_config_manager.get_config.assert_any_call('target_branch')
    mock_config_manager.get_config.assert_any_call('assignee_id')

    assert gitlab_api.assignee_id == 12345
    assert gitlab_api.target_branch == 'main'


def test_get_current_branch_success(mock_subprocess_run_success, mock_merge_requests, mock_config_manager):
    """
    Test that get_current_branch returns the current branch name successfully.
    """
    # Arrange
    mock_subprocess_run_success.return_value = mock_subprocess_run_output("feature-branch\n")

    gitlab_api = Gitlab_api()

    # Act
    branch = gitlab_api.get_current_branch()

    # Assert
    assert branch == "feature-branch"

    mock_subprocess_run_success.assert_called_with(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )


def test_get_current_branch_failure(mock_subprocess_run_failure, mock_merge_requests, mock_config_manager):
    """
    Test that get_current_branch propagates the CalledProcessError when subprocess fails.
    """
    gitlab_api = Gitlab_api()

    # Act & Assert
    with pytest.raises(subprocess.CalledProcessError):
        gitlab_api.get_current_branch()


def test_get_api_url_https(gitlab_api, mock_subprocess_run_success):
    """
    Test the get_api_url method to ensure it constructs the correct API URL
    when the stdout returns an HTTPS repo URL.
    """
    # Given
    mock_subprocess_run_success.return_value = mock_subprocess_run_output(
        "https://gitlab.com/owner/repo.git")
    # When
    api_url = gitlab_api.get_api_url()

    # Then
    assert api_url == 'https://gitlab.com/api/v4/projects/owner%2Frepo/merge_requests'


def test_get_api_url_ssh(gitlab_api, mock_subprocess_run_success):
    """
    Test the get_api_url method to ensure it constructs the correct API URL
    when using SSH remote URL.
    """
    # Given
    mock_subprocess_run_success.return_value = mock_subprocess_run_output(
        "git@gitlab.com:owner/repo.git")

    # When
    api_url = gitlab_api.get_api_url()

    # Then
    assert api_url == 'https://gitlab.com/api/v4/projects/owner%2Frepo/merge_requests'


def test_create_merge_request_existing_mr_not_found(mock_requests_get, mock_requests_post, mock_merge_requests, mock_subprocess_run_success):
    """
    Test that create_merge_request handles existing merge requests appropriately.
    """
    # Arrange
    gitlab_api = Gitlab_api()
    gitlab_api.repo_owner = "owner"
    gitlab_api.repo_name = "repo"
    gitlab_api.target_branch = "main"
    gitlab_api.assignee_id = 12345
    gitlab_api.iid = 1
    gitlab_api.get_current_branch = MagicMock(return_value="feature-branch")
    gitlab_api.get_api_key = MagicMock(return_value="test_gitlab_token")

    # Response indicating no existing PR
    gitlab_api.get_existing_merge_request = MagicMock(return_value=None)

    # Response indicating successful create
    mock_response_post = Mock()
    mock_response_post.status_code = 201
    mock_response_post.json.return_value = {
        'id': 1, 'iid': 1, 'url': 'https://gitlab.com/owner/repo/-/merge_requests', 'state': 'opened'
    }
    mock_requests_post.return_value = mock_response_post

    # Act
    with patch('builtins.print') as mock_print:
        gitlab_api.create_merge_request("Title", "description")

    # Assert
    mock_requests_post.assert_called_once_with(
        gitlab_api.get_api_url(),
        headers={"PRIVATE-TOKEN": "test_gitlab_token"},
        json={
            "source_branch": "feature-branch",
            "target_branch": gitlab_api.target_branch,
            "title": "Title",
            "description": "description",
            "assignee_id": gitlab_api.assignee_id,
            "remove_source_branch": True,
            "squash": True
        }
    )
    mock_print.assert_any_call("Merge request created successfully with internal ID: 1")


def test_create_merge_request_existing_mr(mock_requests_get, mock_requests_put, mock_merge_requests, mock_subprocess_run_success):
    """
    Test that create_merge_request handles existing merge requests appropriately.
    """
    # Arrange
    gitlab_api = Gitlab_api()
    gitlab_api.repo_owner = "owner"
    gitlab_api.repo_name = "repo"
    gitlab_api.target_branch = "main"
    gitlab_api.assignee_id = 12345
    gitlab_api.get_current_branch = MagicMock(return_value="feature-branch")
    gitlab_api.get_api_key = MagicMock(return_value="test_gitlab_token")
    gitlab_api.iid = 1
    # Response indicating existing PR
    mock_response_get = Mock()
    mock_response_get.status_code = 200
    mock_response_get.json.return_value = [{
        'iid': 1,
        'web_url': 'https://gitlab.com/owner/repo/-/merge_requests/1',
        'state': 'opened'
    }]
    mock_requests_get.return_value = mock_response_get

    # Response indicating successful update
    mock_response_put = Mock()
    mock_response_put.status_code = 200
    mock_response_put.json.return_value = {'iid': 1}
    mock_requests_put.return_value = mock_response_put

    # Act
    with patch('builtins.print') as mock_print:
        gitlab_api.create_merge_request("Title", "Updated description")

    # Assert
    mock_requests_get.assert_called_once()

    mock_requests_put.assert_called_once_with(
        f"{gitlab_api.get_api_url()}/{1}",
        headers={"PRIVATE-TOKEN": "test_gitlab_token"},
        json={
            "title": "Title",
            "description": "Updated description",
            "remove_source_branch": True,
            "squash": True
        }
    )
    mock_print.assert_any_call("A merge request already exists: https://gitlab.com/owner/repo/-/merge_requests/1")
    mock_print.assert_any_call("Merge request updated successfully with internal ID: 1")


def test_update_merge_request_failure(mock_requests_get, mock_requests_put):
    """
    Test that update_merge_request handles failures appropriately.
    """
    # Arrange
    gitlab_api = Gitlab_api()
    gitlab_api.get_api_key = MagicMock(return_value="test_gitlab_token")

    mock_response_put = MagicMock()
    mock_response_put.status_code = 400
    mock_response_put.text = '{"message": "Bad Request"}'
    mock_requests_put.return_value = mock_response_put

    with patch('builtins.print') as mock_print:
        # Act
        gitlab_api.update_merge_request(1, "Title", "Description")

    # Assert
    mock_requests_put.assert_called_once()
    mock_print.assert_any_call("Failed to update merge request: 400")
    mock_print.assert_any_call('Response text: {"message": "Bad Request"}')
