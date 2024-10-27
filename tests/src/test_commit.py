import pytest
import subprocess
from unittest.mock import patch, Mock

from gai.src.commit import Commit

# --------------------------
# Fixtures
# --------------------------


@pytest.fixture
def mock_subprocess_run_success():
    """
    Fixture to mock subprocess.run for successful executions.
    Returns a mock that can be configured per test.
    """
    with patch('gai.src.commit.subprocess.run') as mock_run:
        yield mock_run


@pytest.fixture
def mock_subprocess_run_failure():
    """
    Fixture to mock subprocess.run to raise CalledProcessError.
    """
    with patch('gai.src.commit.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ['git', 'command'])
        yield mock_run


@pytest.fixture
def commit_instance():
    """
    Fixture to provide a fresh instance of Commit for tests.
    """
    return Commit()

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
# format_commits Method Tests
# --------------------------


def test_format_commits(commit_instance):
    result = "commit1\ncommit2\ncommit3"
    expected = "Changes:\n- commit1\n- commit2\n- commit3"
    assert commit_instance.format_commits(
        result) == expected, "Should format commits correctly"

# --------------------------
# get_commits Method Tests
# --------------------------


def test_get_commits_success(mock_subprocess_run_success, commit_instance):
    # Mock the fetch command
    mock_fetch = mock_subprocess_run_output("", 0)
    # Mock the log command
    mock_log = mock_subprocess_run_output("commit1\ncommit2", 0)
    mock_subprocess_run_success.side_effect = [mock_fetch, mock_log]

    commits = commit_instance.get_commits("origin", "main", "feature-branch")
    assert commits == "commit1\ncommit2", "Should return the fetched commits"

    mock_subprocess_run_success.assert_any_call(
        ["git", "fetch", "origin"],
        check=True,
        capture_output=True
    )

    mock_subprocess_run_success.assert_any_call(
        ["git", "log", "--oneline", "origin/main..feature-branch"],
        capture_output=True,
        text=True,
        check=True
    )


def test_get_commits_fetch_failure(mock_subprocess_run_failure, commit_instance):
    commits = commit_instance.get_commits("origin", "main", "feature-branch")
    assert commits.startswith(
        "Error fetching commits:"), "Should return error message on fetch failure"


def test_get_commits_log_failure(mock_subprocess_run_success, commit_instance):
    # Mock the fetch command
    mock_fetch = mock_subprocess_run_output("", 0)
    # Mock the log command to fail
    mock_subprocess_run_success.side_effect = [
        mock_fetch,
        subprocess.CalledProcessError(
            1,
            ["git", "log", "--oneline", "origin/main..feature-branch"],
            output="",
            stderr="fatal: bad revision 'origin/main..feature-branch'"
        )
    ]

    commits = commit_instance.get_commits("origin", "main", "feature-branch")
    expected_error = ("Error fetching commits: Command '['git', 'log', '--oneline', "
                      "'origin/main..feature-branch']' returned non-zero exit status 1.")
    assert commits == expected_error, "Should return specific error message on log failure"

    # Verify fetch command was called
    mock_subprocess_run_success.assert_any_call(
        ["git", "fetch", "origin"],
        check=True,
        capture_output=True
    )
    # Verify log command was called
    mock_subprocess_run_success.assert_any_call(
        ["git", "log", "--oneline", "origin/main..feature-branch"],
        capture_output=True,
        text=True,
        check=True
    )
