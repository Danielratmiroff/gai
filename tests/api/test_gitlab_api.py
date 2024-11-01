import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import subprocess
import requests

from gai.api import Gitlab_api


@pytest.fixture
def mock_merge_requests():
    """
    Fixture to mock the Merge_requests class in gai.src.
    """
    with patch('gai.src.merge_requests.Merge_requests') as MockMergeRequests:
        mock_instance = MagicMock()

        MockMergeRequests.return_value = mock_instance
        MockMergeRequests._instance = mock_instance
        yield mock_instance


@pytest.fixture
def gitlab_api(mock_merge_requests):
    """
    Fixture to initialize the Gitlab_api instance with mocked Merge_requests.
    """
    return Gitlab_api()


def test_load_config(gitlab_api):
    """
    Test the load_config method to ensure configuration is loaded correctly.
    """
    # Given
    mock_config_manager = MagicMock()
    mock_config_manager.get_config.side_effect = [
        'main',
        12345
    ]

    with patch('gai.api.gitlab_api.ConfigManager', return_value=mock_config_manager) as mock_config_manager_class:
        with patch('gai.api.gitlab_api.get_app_name', return_value='test_app'):
            # When
            gitlab_api.load_config()

            # Then
            mock_config_manager_class.assert_called_once_with('test_app')
            mock_config_manager.get_config.assert_any_call('target_branch')
            mock_config_manager.get_config.assert_any_call('assignee_id')

            assert gitlab_api.target_branch == 'main'
            assert gitlab_api.assignee_id == 12345


def test_get_api_key_success(gitlab_api):
    """
    Test the get_api_key method when GITLAB_PRIVATE_TOKEN is set.
    """
    # Given
    with patch.dict(os.environ, {'GITLAB_PRIVATE_TOKEN': 'test_gitlab_token'}):
        # When
        api_key = gitlab_api.get_api_key()

        # Then
        assert api_key == 'test_gitlab_token'


def test_get_api_key_failure(gitlab_api):
    """
    Test the get_api_key method when GITLAB_PRIVATE_TOKEN is not set.
    """
    # Given
    with patch.dict(os.environ, {}, clear=True):
        # When
        with pytest.raises(ValueError) as exc_info:
            gitlab_api.get_api_key()

        # Then
        assert "GITLAB_PRIVATE_TOKEN is not set" in str(exc_info.value)


def test_get_current_branch(gitlab_api):
    """
    Test the get_current_branch method to ensure it retrieves the correct branch name.
    """

    # Given
    with patch('gai.api.gitlab_api.subprocess.run') as mock_subprocess_run:
        mock_result = MagicMock()
        mock_result.stdout = 'feature-branch\n'
        mock_subprocess_run.return_value = mock_result

        # when
        current_branch = gitlab_api.get_current_branch()

        # Then
        mock_subprocess_run.assert_called_once_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True
        )
        assert current_branch == 'feature-branch'


def test_construct_project_url_https(gitlab_api, mock_merge_requests):
    """
    Test the construct_project_url method to ensure it constructs the correct project URL
    when the stdout returns an HTTPS repo URL.
    """

    # Given
    with patch('gai.api.gitlab_api.subprocess.run') as mock_subprocess_run:
        mock_result = MagicMock()
        mock_result.stdout = 'https://gitlab.com/owner/repo.git\n'
        mock_subprocess_run.return_value = mock_result

        # When
        project_url = gitlab_api.construct_project_url()

        # Then
        assert project_url == 'owner%2Frepo'


def test_construct_project_url(gitlab_api, mock_merge_requests):
    """
    Test the construct_project_url method to ensure it constructs the correct project URL.
    """

    # Given
    with patch('gai.api.gitlab_api.subprocess.run') as mock_subprocess_run:
        mock_result = MagicMock()
        mock_result.stdout = 'git@gitlab.com:owner/repo.git\n'
        mock_subprocess_run.return_value = mock_result

        # When
        project_url = gitlab_api.construct_project_url()

        # Then
        assert project_url == 'owner%2Frepo'


def test_create_merge_request_existing_mr(mock_merge_requests):
    """
    Test that create_merge_request handles existing merge requests appropriately.
    """
    # Arrange
    gitlab_api = Gitlab_api()
    gitlab_api.get_current_branch = MagicMock(return_value="feature-branch")
    gitlab_api.get_api_key = MagicMock(return_value="test_gitlab_token")

    with patch('gai.api.gitlab_api.requests.get') as mock_requests_get:
        mock_response_get = MagicMock()
        mock_response_get.status_code = 200
        mock_response_get.json.return_value = [{
            'iid': 1,
            'web_url': 'https://gitlab.com/owner/repo/-/merge_requests/1'
        }]
        mock_requests_get.return_value = mock_response_get

        with patch('gai.api.gitlab_api.requests.put') as mock_requests_put:
            mock_response_put = MagicMock()
            mock_response_put.status_code = 200
            mock_requests_put.return_value = mock_response_put

            with patch('builtins.print') as mock_print:
                # Act
                gitlab_api.create_merge_request("Title", "Updated description")

    # Assert
    mock_requests_get.assert_called_once()
    mock_requests_put.assert_called_once_with(
        "https://gitlab.com/api/v4/projects/owner%2Frepo/merge_requests/1",
        headers={"PRIVATE-TOKEN": "test_gitlab_token"},
        json={"title": "Title", "description": "Updated description"}
    )
    mock_print.assert_any_call("A merge request already exists: https://gitlab.com/owner/repo/-/merge_requests/1")
    mock_print.assert_any_call("Merge request updated successfully.")


def test_update_merge_request_failure(mock_merge_requests):
    """
    Test that update_merge_request handles failures appropriately.
    """
    # Arrange
    gitlab_api = Gitlab_api()
    gitlab_api.get_api_key = MagicMock(return_value="test_gitlab_token")

    with patch('gai.api.gitlab_api.requests.put') as mock_requests_put:
        mock_response_put = MagicMock()
        mock_response_put.status_code = 400
        mock_response_put.json.return_value = {"message": "Bad Request"}
        mock_requests_put.return_value = mock_response_put

        with patch('builtins.print') as mock_print:
            # Act
            gitlab_api.update_merge_request(
                "owner%2Frepo", 1, "Title", "Description")

    # Assert
    mock_requests_put.assert_called_once()
    mock_print.assert_any_call("Failed to update merge request: 400")
    mock_print.assert_any_call("Response text: {'message': 'Bad Request'}")
