import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import subprocess
import requests

# Adjust the import path based on your project structure
from gai.api import Github_api


@pytest.fixture
def mock_merge_requests():
    """
    Fixture to mock the Merge_requests class in gai.api.github_api.
    """
    with patch('gai.api.github_api.Merge_requests') as MockMergeRequests:
        mock_instance = MockMergeRequests.return_value
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
    with patch("builtins.open", mock_open(read_data="target_branch: main")) as mock_file:
        with patch("gai.api.github_api.yaml.safe_load") as mock_yaml_load:
            # Configure the mock to return a specific configuration
            mock_yaml_load.return_value = {'target_branch': 'main'}

            # Call the method under test
            github_api.load_config()

            # Assertions to ensure config is loaded correctly
            mock_file.assert_called_once_with("gai/config.yaml", "r")
            mock_yaml_load.assert_called_once()
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


def test_get_current_branch(github_api):
    """
    Test the get_current_branch method to ensure it retrieves the correct branch name.
    """
    with patch('gai.api.github_api.subprocess.run') as mock_subprocess_run:
        # Given
        mock_result = MagicMock()
        mock_result.stdout = 'feature-branch\n'
        mock_subprocess_run.return_value = mock_result

        # When
        current_branch = github_api.get_current_branch()

        # Then
        mock_subprocess_run.assert_called_once_with(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True
        )
        assert current_branch == 'feature-branch'


def test_create_pull_request_success(github_api, mock_merge_requests):
    """
    Test the create_pull_request method for a successful pull request creation.
    """
    # Given
    # TODO: this test should cover the "get repo owner" and "get repo" methods
    mock_merge_requests.get_repo_owner_from_remote_url.return_value = 'owner'
    mock_merge_requests.get_repo_from_remote_url.return_value = 'repo'

    with patch.object(Github_api, 'get_current_branch', return_value='feature-branch') as mock_get_branch:
        with patch.object(Github_api, 'get_api_key', return_value='test_token') as mock_get_api_key:

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
    mock_merge_requests.get_repo_owner_from_remote_url.return_value = 'owner'
    mock_merge_requests.get_repo_from_remote_url.return_value = 'repo'

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
