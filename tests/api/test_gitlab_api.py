import pytest
from unittest.mock import Mock, patch, MagicMock
import os
import subprocess
import gitlab

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
def mock_gitlab_client():
    """
    Fixture to mock the GitLab client and project.
    """
    with patch('gai_tool.api.gitlab_api.gitlab.Gitlab') as mock_gitlab_class:
        mock_gitlab_instance = Mock()
        mock_gitlab_class.return_value = mock_gitlab_instance

        # Mock project
        mock_project = Mock()
        mock_gitlab_instance.projects.get.return_value = mock_project

        # Mock merge requests manager
        mock_mr_manager = Mock()
        mock_project.mergerequests = mock_mr_manager

        yield {
            'gitlab_class': mock_gitlab_class,
            'gitlab_instance': mock_gitlab_instance,
            'project': mock_project,
            'mr_manager': mock_mr_manager
        }


@pytest.fixture
def gitlab_api(mock_merge_requests, mock_config_manager, mock_get_app_name, mock_gitlab_client):
    """
    Fixture to initialize the Gitlab_api instance with mocked dependencies.
    """
    with patch.dict(os.environ, {'GITLAB_PRIVATE_TOKEN': 'test_token'}):
        return Gitlab_api()


@pytest.fixture
def mock_subprocess_run_success():
    """
    Fixture to mock subprocess.run for successful executions.
    Returns a mock that can be configured per test.
    """
    with patch('gai_tool.api.gitlab_api.subprocess.run') as mock_run:
        yield mock_run


@pytest.fixture
def mock_subprocess_run_failure():
    """
    Fixture to mock subprocess.run to raise CalledProcessError.
    """
    with patch('gai_tool.api.gitlab_api.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['git', 'command'])
        yield mock_run


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
    mock_config_manager.get_config.assert_any_call('target_branch')
    mock_config_manager.get_config.assert_any_call('assignee_id')

    assert gitlab_api.assignee_id == 12345
    assert gitlab_api.target_branch == 'main'


def test_get_current_branch_success(mock_subprocess_run_success, gitlab_api):
    """
    Test that get_current_branch returns the current branch name successfully.
    """
    # Arrange
    mock_subprocess_run_success.return_value = mock_subprocess_run_output("feature-branch\n")

    # Act
    branch = gitlab_api.get_current_branch()

    # Assert
    assert branch == "feature-branch"

    mock_subprocess_run_success.assert_called_with(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )


def test_get_current_branch_failure(mock_subprocess_run_failure, gitlab_api):
    """
    Test that get_current_branch propagates the CalledProcessError when subprocess fails.
    """
    # Act & Assert
    with pytest.raises(subprocess.CalledProcessError):
        gitlab_api.get_current_branch()


def test_initialize_gitlab_client(gitlab_api, mock_gitlab_client):
    """
    Test that the GitLab client is initialized correctly.
    """
    # Assert
    mock_gitlab_client['gitlab_class'].assert_called_once_with(
        "https://gitlab.com",
        private_token="test_token"
    )
    mock_gitlab_client['gitlab_instance'].projects.get.assert_called_once_with("owner/repo")


def test_get_api_key_success():
    """
    Test that get_api_key returns the token from environment variables.
    """
    with patch.dict(os.environ, {'GITLAB_PRIVATE_TOKEN': 'test_token'}):
        with patch('gai_tool.api.gitlab_api.Merge_requests'), \
                patch('gai_tool.api.gitlab_api.ConfigManager'), \
                patch('gai_tool.api.gitlab_api.get_app_name'), \
                patch('gai_tool.api.gitlab_api.gitlab.Gitlab'):
            gitlab_api = Gitlab_api()
            api_key = gitlab_api.get_api_key()
            assert api_key == "test_token"


def test_get_api_key_not_set():
    """
    Test that get_api_key raises ValueError when token is not set.
    """
    with patch.dict(os.environ, {}, clear=True):
        with patch('gai_tool.api.gitlab_api.Merge_requests'), \
                patch('gai_tool.api.gitlab_api.ConfigManager'), \
                patch('gai_tool.api.gitlab_api.get_app_name'):
            # The constructor will fail during initialization due to missing token
            with pytest.raises(ValueError, match="GITLAB_PRIVATE_TOKEN is not set"):
                Gitlab_api()


def test_get_existing_merge_request_found(gitlab_api, mock_gitlab_client):
    """
    Test that get_existing_merge_request returns MR data when found.
    """
    # Arrange
    mock_mr = Mock()
    mock_mr._attrs = {
        'iid': 1,
        'web_url': 'https://gitlab.com/owner/repo/-/merge_requests/1',
        'state': 'opened'
    }
    mock_gitlab_client['mr_manager'].list.return_value = [mock_mr]

    # Act
    result = gitlab_api.get_existing_merge_request("feature-branch")

    # Assert
    assert result == mock_mr._attrs
    mock_gitlab_client['mr_manager'].list.assert_called_once_with(
        source_branch="feature-branch",
        state='opened',
        all=True
    )


def test_get_existing_merge_request_not_found(gitlab_api, mock_gitlab_client):
    """
    Test that get_existing_merge_request returns None when no MR found.
    """
    # Arrange
    mock_gitlab_client['mr_manager'].list.return_value = []

    # Act
    result = gitlab_api.get_existing_merge_request("feature-branch")

    # Assert
    assert result is None
    mock_gitlab_client['mr_manager'].list.assert_called_once_with(
        source_branch="feature-branch",
        state='opened',
        all=True
    )


def test_get_existing_merge_request_gitlab_error(gitlab_api, mock_gitlab_client):
    """
    Test that get_existing_merge_request handles GitLab errors gracefully.
    """
    # Arrange
    mock_gitlab_client['mr_manager'].list.side_effect = gitlab.exceptions.GitlabError("API Error")

    # Act
    with patch('builtins.print') as mock_print:
        result = gitlab_api.get_existing_merge_request("feature-branch")

    # Assert
    assert result is None
    mock_print.assert_called_once_with("Error fetching merge requests: API Error")


def test_update_merge_request_success(gitlab_api, mock_gitlab_client):
    """
    Test that update_merge_request updates an existing MR successfully.
    """
    # Arrange
    mock_mr = Mock()
    mock_gitlab_client['mr_manager'].get.return_value = mock_mr

    # Act
    with patch('builtins.print') as mock_print:
        gitlab_api.update_merge_request(1, "New Title", "New Description")

    # Assert
    mock_gitlab_client['mr_manager'].get.assert_called_once_with(1)
    assert mock_mr.title == "New Title"
    assert mock_mr.description == "New Description"
    assert mock_mr.remove_source_branch is True
    assert mock_mr.squash is True
    mock_mr.save.assert_called_once()
    mock_print.assert_called_once_with("Merge request updated successfully with internal ID: 1")


def test_update_merge_request_failure(gitlab_api, mock_gitlab_client):
    """
    Test that update_merge_request handles failures appropriately.
    """
    # Arrange
    mock_gitlab_client['mr_manager'].get.side_effect = gitlab.exceptions.GitlabError("Update failed")

    # Act
    with patch('builtins.print') as mock_print:
        gitlab_api.update_merge_request(1, "Title", "Description")

    # Assert
    mock_print.assert_called_once_with("Failed to update merge request: Update failed")


def test_create_merge_request_new_mr(gitlab_api, mock_gitlab_client, mock_subprocess_run_success):
    """
    Test that create_merge_request creates a new MR when none exists.
    """
    # Arrange
    mock_subprocess_run_success.return_value = mock_subprocess_run_output("feature-branch\n")

    # Mock no existing MR
    mock_gitlab_client['mr_manager'].list.return_value = []

    # Mock successful creation
    mock_new_mr = Mock()
    mock_new_mr.iid = 1
    mock_new_mr.web_url = "https://gitlab.com/owner/repo/-/merge_requests/1"
    mock_gitlab_client['mr_manager'].create.return_value = mock_new_mr

    # Act
    with patch('builtins.print') as mock_print:
        gitlab_api.create_merge_request("Test Title", "Test Description")

    # Assert
    mock_gitlab_client['mr_manager'].create.assert_called_once_with({
        "source_branch": "feature-branch",
        "target_branch": "main",
        "title": "Test Title",
        "description": "Test Description",
        "remove_source_branch": True,
        "squash": True,
        "assignee_id": 12345
    })

    mock_print.assert_any_call("Merge request created successfully with internal ID: 1")
    mock_print.assert_any_call("URL: https://gitlab.com/owner/repo/-/merge_requests/1")


def test_create_merge_request_existing_mr(gitlab_api, mock_gitlab_client, mock_subprocess_run_success):
    """
    Test that create_merge_request updates existing MR when found.
    """
    # Arrange
    mock_subprocess_run_success.return_value = mock_subprocess_run_output("feature-branch\n")

    # Mock existing MR
    mock_existing_mr = Mock()
    mock_existing_mr._attrs = {
        'iid': 1,
        'web_url': 'https://gitlab.com/owner/repo/-/merge_requests/1',
        'state': 'opened'
    }
    mock_gitlab_client['mr_manager'].list.return_value = [mock_existing_mr]

    # Mock get for update
    mock_mr_for_update = Mock()
    mock_gitlab_client['mr_manager'].get.return_value = mock_mr_for_update

    # Act
    with patch('builtins.print') as mock_print:
        gitlab_api.create_merge_request("Updated Title", "Updated Description")

    # Assert
    # Should not call create
    mock_gitlab_client['mr_manager'].create.assert_not_called()

    # Should call update
    mock_gitlab_client['mr_manager'].get.assert_called_once_with(1)
    assert mock_mr_for_update.title == "Updated Title"
    assert mock_mr_for_update.description == "Updated Description"
    mock_mr_for_update.save.assert_called_once()

    mock_print.assert_any_call("A merge request already exists: https://gitlab.com/owner/repo/-/merge_requests/1")
    mock_print.assert_any_call("Merge request updated successfully with internal ID: 1")


def test_create_merge_request_creation_failure(gitlab_api, mock_gitlab_client, mock_subprocess_run_success):
    """
    Test that create_merge_request handles creation failures.
    """
    # Arrange
    mock_subprocess_run_success.return_value = mock_subprocess_run_output("feature-branch\n")
    mock_gitlab_client['mr_manager'].list.return_value = []
    mock_gitlab_client['mr_manager'].create.side_effect = gitlab.exceptions.GitlabCreateError("Creation failed")

    # Act
    with patch('builtins.print') as mock_print:
        gitlab_api.create_merge_request("Test Title", "Test Description")

    # Assert
    mock_print.assert_called_once_with("Failed to create merge request: Creation failed")
