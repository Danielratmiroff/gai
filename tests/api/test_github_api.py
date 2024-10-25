import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import subprocess
import requests

# Adjust the import path based on your project structure
from gai.api import Github_api
from tests.test_helpers import mock_subprocess_run_output


@pytest.fixture
def mr_mock_subprocess_run_success():
    """
    Fixture to mock subprocess.run for successful executions.
    Returns a mock that can be configured per test.
    """
    with patch('gai.src.merge_requests.subprocess.run') as mock_run:
        yield mock_run


@pytest.fixture
def mock_merge_requests():
    """
    Fixture to mock the Merge_requests class in gai.src.
    """
    with patch('gai.src.merge_requests.Merge_requests') as MockMergeRequests:
        mock_instance = MagicMock()
        mock_instance.git_repo_url.return_value = 'git@gitlab.com:owner/repo.git'
        mock_instance.get_remote_url.return_value = 'gitlab.com'  # Add explicit return value
        mock_instance.get_repo_owner_from_remote_url.return_value = 'owner'
        mock_instance.get_repo_from_remote_url.return_value = 'repo'

        MockMergeRequests.return_value = mock_instance
        MockMergeRequests._instance = mock_instance
        yield mock_instance


@pytest.fixture
def github_api(mock_merge_requests):
    """
    Fixture to initialize the Github_api instance with mocked Merge_requests.
    """
    return Github_api()


def test_load_config(github_api):
    """
    Test the load_config method to ensure configuration is loaded correctly.
    """
    # Given
    mock_config_manager = MagicMock()
    mock_config_manager.get_config.side_effect = [
        'main',
        '12345'
    ]

    with patch('gai.api.github_api.ConfigManager', return_value=mock_config_manager) as mock_config_manager_class:
        with patch('gai.api.github_api.get_app_name', return_value='test_app'):
            # When
            github_api.load_config()

            # Then
            mock_config_manager_class.assert_called_once_with('test_app')
            mock_config_manager.get_config.assert_any_call('target_branch')
            assert github_api.target_branch == 'main'


def test_get_api_key_success(github_api):
    """
    Test the get_api_key method when GITHUB_TOKEN is set.
    """
    with patch.dict(os.environ, {'GITHUB_TOKEN': 'test_token'}):
        api_key = github_api.get_api_key()

        assert api_key == 'test_token'


def test_get_api_key_failure(github_api):
    """
    Test the get_api_key method when GITHUB_TOKEN is not set.
    """
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError) as exc_info:
            github_api.get_api_key()

        assert "GITHUB_TOKEN is not set" in str(exc_info.value)


def test_get_current_branch(mr_mock_subprocess_run_success, github_api):
    """
    Test the get_current_branch method to ensure it retrieves the correct branch name.
    """
    mr_mock_subprocess_run_success.return_value = mock_subprocess_run_output(
        'feature-branch\n')

    # When
    current_branch = github_api.get_current_branch()
    print(current_branch)

    # Then
    mr_mock_subprocess_run_success.assert_called_with(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, check=True
    )

    assert current_branch == 'feature-branch'


def test_create_pull_request_success(github_api, mock_merge_requests, mr_mock_subprocess_run_success):
    """
    Test the create_pull_request method for a successful pull request creation.
    """
    # Given
    mr_mock_subprocess_run_success.return_value = mock_subprocess_run_output(
        'git@github.com:owner/repo.git')

    with patch.object(Github_api, 'get_current_branch', return_value='feature-branch'):
        with patch.object(Github_api, 'get_api_key', return_value='test_token'):

            # Configure the mock response for a successful PR creation
            with patch('gai.api.github_api.requests.post') as mock_requests_post:
                mock_response = MagicMock()
                mock_response.status_code = 201
                mock_response.json.return_value = {
                    'html_url': 'https://github.com/owner/repo/pull/1'
                }
                mock_requests_post.return_value = mock_response

                # Capture the print output
                with patch('builtins.print') as mock_print:
                    # When
                    github_api.create_pull_request('Test PR', 'Test body')

                    mock_requests_post.assert_called_once_with(
                        "https://api.github.com/repos/owner/repo/pulls",
                        headers={
                            "Authorization": "token test_token",
                            "Accept": "application/vnd.github.v3+json"
                        },
                        json={
                            "title": "Test PR",
                            "head": "feature-branch",
                            "base": github_api.target_branch,
                            "body": "Test body"
                        }
                    )

                    # Then
                    mock_print.assert_any_call(
                        "Pull request created successfully.")
                    mock_print.assert_any_call(
                        "Pull request URL: https://github.com/owner/repo/pull/1")


def test_create_pull_request_failure(github_api, mock_merge_requests):
    """
    Test the create_pull_request method when pull request creation fails.
    """
    # Given
    with patch('gai.src.merge_requests.subprocess.run') as mock_subprocess_run:
        mock_result = MagicMock()
        # Simulate the output of the command
        mock_result.stdout = 'git@github.com:owner/repo.git'
        mock_subprocess_run.return_value = mock_result

        with patch.object(Github_api, 'get_current_branch', return_value='feature-branch') as mock_get_branch:
            with patch.object(Github_api, 'get_api_key', return_value='test_token') as mock_get_api_key:

                # Configure the mock response for a failed PR creation
                with patch('gai.api.github_api.requests.post') as mock_requests_post:
                    mock_response = MagicMock()
                    mock_response.status_code = 422
                    mock_response.json.return_value = {
                        'message': 'Validation Failed'}
                    mock_requests_post.return_value = mock_response

                    # Capture the print output
                    with patch('builtins.print') as mock_print:

                        # When
                        github_api.create_pull_request('Test PR', 'Test body')

                        mock_requests_post.assert_called_once_with(
                            "https://api.github.com/repos/owner/repo/pulls",
                            headers={
                                "Authorization": "token test_token",
                                "Accept": "application/vnd.github.v3+json"
                            },
                            json={
                                "title": "Test PR",
                                "head": "feature-branch",
                                "base": github_api.target_branch,
                                "body": "Test body"
                            }
                        )

                        # Then
                        mock_print.assert_any_call(
                            "Failed to create pull request: 422")
                        mock_print.assert_any_call(
                            "Error message: {'message': 'Validation Failed'}")
