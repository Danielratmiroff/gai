import pytest
import subprocess
from unittest.mock import patch, Mock

from gai.src.merge_requests import Merge_requests, parse_repo_name, parse_repo_owner

# --------------------------
# Fixtures
# --------------------------


@pytest.fixture(autouse=True)
def reset_singleton():
    """
    Fixture to reset the singleton instance before each test.
    Ensures that each test has a fresh instance of Merge_requests.
    """
    if hasattr(Merge_requests, '_instance'):
        del Merge_requests._instance


@pytest.fixture
def mock_subprocess_run_success():
    """
    Fixture to mock subprocess.run for successful executions.
    Returns a mock that can be configured per test.
    """
    with patch('gai.src.merge_requests.subprocess.run') as mock_run:
        yield mock_run


@pytest.fixture
def mock_subprocess_run_failure():
    """
    Fixture to mock subprocess.run to raise CalledProcessError.
    """
    with patch('gai.src.merge_requests.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['git', 'command'])
        yield mock_run


@pytest.fixture
def merge_requests_instance():
    """
    Fixture to provide a fresh instance of Merge_requests for tests.
    """
    return Merge_requests()

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
# Singleton Behavior Tests
# --------------------------


def test_singleton_get_instance_default():
    mr1 = Merge_requests.get_instance()
    mr2 = Merge_requests.get_instance()
    assert mr1 is mr2, "get_instance should return the same singleton instance"
    assert mr1.remote_name == "origin", "Default remote_name should be 'origin'"


def test_singleton_get_instance_custom_remote():
    mr1 = Merge_requests.get_instance(remote_name="upstream")
    mr2 = Merge_requests.get_instance()
    assert mr1 is mr2, "get_instance should return the same singleton instance"
    assert mr1.remote_name == "upstream", "remote_name should be updated to 'upstream'"


def test_singleton_initialize():
    mr1 = Merge_requests.get_instance()
    mr2 = Merge_requests.initialize(remote_name="upstream")
    assert mr1 is not mr2, "initialize should create a new instance"
    assert mr2.remote_name == "upstream", "New instance should have remote_name 'upstream'"

# --------------------------
# git_repo_url Method Tests
# --------------------------


def test_git_repo_ssh_success(mock_subprocess_run_success, merge_requests_instance):
    mock_subprocess_run_success.return_value = mock_subprocess_run_output(
        "git@github.com:user/repo.git")

    url = merge_requests_instance.git_repo_url()

    assert url == "github.com/user/repo.git", f"Should return the correct remote URL"

    mock_subprocess_run_success.assert_called_with(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True
    )


def test_git_repo_url_success(mock_subprocess_run_success, merge_requests_instance):
    mock_subprocess_run_success.return_value = mock_subprocess_run_output(
        "https://github.com/user/repo.git")

    url = merge_requests_instance.git_repo_url()

    assert url == "github.com/user/repo.git", "Should return the correct remote URL"

    mock_subprocess_run_success.assert_called_with(
        ["git", "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
        check=True
    )


def test_git_repo_url_failure(mock_subprocess_run_failure):
    mr = Merge_requests()
    url = mr.git_repo_url()
    assert url == "Error: Unable to get remote URL. Make sure you're in a git repository.", "Should return error message on failure"

# --------------------------
# get_repo_owner_from_remote_url Method Tests
# --------------------------


def test_parse_repo_owner_success():
    url = 'github.com/owner/repo.git'
    assert parse_repo_owner(url) == "owner"


def test_parse_repo_owner_empty_url():
    with pytest.raises(ValueError, match="Repository URL cannot be empty"):
        parse_repo_owner("")


def test_parse_repo_owner_invalid_format():
    with pytest.raises(ValueError, match="Invalid repository URL format"):
        parse_repo_owner("invalid_url")


def test_parse_repo_owner_empty_domain():
    with pytest.raises(ValueError, match="Invalid repository URL format"):
        parse_repo_owner("/owner/repo.git")


def test_parse_repo_owner_empty_owner():
    with pytest.raises(ValueError, match="Invalid repository URL format"):
        parse_repo_owner("/repo-name")


@patch('gai.src.merge_requests.Merge_requests.git_repo_url')
def test_get_repo_owner_from_remote_url_failure(mock_git_url, merge_requests_instance):
    mock_git_url.return_value = "invalid_url"

    with pytest.raises(ValueError, match="Error: Unable to get repo owner."):
        merge_requests_instance.get_repo_owner_from_remote_url()


@patch('gai.src.merge_requests.Merge_requests.git_repo_url')
def test_get_repo_owner_from_remote_url_success(mock_git_url, merge_requests_instance):
    mock_git_url.return_value = "github.com/owner/repo.git"

    owner = merge_requests_instance.get_repo_owner_from_remote_url()

    assert owner == "owner"

# --------------------------
# get_repo_from_remote_url Method Tests
# --------------------------


def test_parse_repo_name():
    url = "github.com/user/repo.git"
    assert parse_repo_name(url) == "repo"


def test_parse_repo_name_no_git_extension():
    url = "github.com/user/repo"
    assert parse_repo_name(url) == "repo"


def test_parse_repo_name_with_trailing_slash():
    url = "github.com/user/repo/"
    assert parse_repo_name(url) == "repo"


def test_parse_repo_name_empty_url():
    with pytest.raises(ValueError, match="Repository URL cannot be empty"):
        parse_repo_name("")


def test_parse_repo_name_only_owner_ssh():
    with pytest.raises(ValueError, match="URL must contain both owner and repository"):
        parse_repo_name("github.com/user")


def test_parse_repo_name_invalid():
    with pytest.raises(ValueError, match="URL must contain both owner and repository"):
        parse_repo_name("github.com")


@patch('gai.src.merge_requests.Merge_requests.git_repo_url')
def test_get_repo_from_remote_ssh_success(mock_git_url, merge_requests_instance):
    mock_git_url.return_value = "github.com/user/repo.git"
    repo = merge_requests_instance.get_repo_from_remote_url()
    assert repo == "repo", "Should correctly parse the repository name from SSH URL"


@patch('gai.src.merge_requests.Merge_requests.git_repo_url')
def test_get_repo_from_remote_url_success(mock_git_url, merge_requests_instance):
    mock_git_url.return_value = "github.com/user/repo.git"
    repo = merge_requests_instance.get_repo_from_remote_url()
    assert repo == "repo", "Should correctly parse the repository name from HTTPS URL"


@patch('gai.src.merge_requests.Merge_requests.git_repo_url')
def test_get_repo_from_remote_url_failure(mock_git_url, merge_requests_instance):
    mock_git_url.return_value = "invalid_url"
    repo = merge_requests_instance.get_repo_from_remote_url()
    assert repo == "Error: Unable to get repo owner.", "Should return error message for invalid URL"
# --------------------------
# get_remote_url Method Tests
# --------------------------


@patch('gai.src.merge_requests.Merge_requests.git_repo_url')
def test_get_remote_url_https(mock_git_url, merge_requests_instance):
    mock_git_url.return_value = "gitlab.com/user/repo.git"
    domain = merge_requests_instance.get_remote_url()
    assert domain == "gitlab.com", "Should extract domain from HTTPS URL"


# --------------------------
# get_remote_platform Method Tests
# --------------------------


@patch('gai.src.merge_requests.Merge_requests.git_repo_url')
def test_get_remote_platform_github(mock_git_url, merge_requests_instance):
    mock_git_url.return_value = "https://github.com/user/repo.git"
    platform = merge_requests_instance.get_remote_platform()
    assert platform == "github", "Should identify GitHub platform"


@patch('gai.src.merge_requests.Merge_requests.git_repo_url')
def test_get_remote_platform_gitlab(mock_git_url, merge_requests_instance):
    mock_git_url.return_value = "https://gitlab.com/user/repo.git"
    platform = merge_requests_instance.get_remote_platform()
    assert platform == "gitlab", "Should identify GitLab platform"


@patch('gai.src.merge_requests.Merge_requests.git_repo_url')
def test_get_remote_platform_unknown(mock_git_url, merge_requests_instance):
    mock_git_url.return_value = "https://bitbucket.org/user/repo.git"
    platform = merge_requests_instance.get_remote_platform()
    expected_error = "Error: Unable to determine platform from remote URL. Only github and gitlab are supported."
    assert platform == expected_error, "Should return error message for unsupported platforms"
