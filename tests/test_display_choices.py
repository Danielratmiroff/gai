# test_display_choices.py

import pytest
from unittest.mock import patch, Mock
import ast

from gai.src.display_choices import DisplayChoices

# --------------------------
# Fixtures
# --------------------------


@pytest.fixture
def display_choices_instance():
    """
    Fixture to provide a fresh instance of DisplayChoices for tests.
    """
    return DisplayChoices()


@pytest.fixture
def mock_pick_success():
    """
    Fixture to mock the pick function for successful selections.
    """
    with patch('gai.src.display_choices.pick') as mock_pick:
        yield mock_pick


@pytest.fixture
def mock_pick_exit():
    """
    Fixture to mock the pick function selecting the EXIT option.
    """
    with patch('gai.src.display_choices.pick') as mock_pick:
        mock_pick.return_value = ("> Exit", None)
        yield mock_pick


@pytest.fixture
def mock_ai_client():
    """
    Fixture to mock the ai_client callable.
    """
    with patch('gai.src.display_choices.ai_client') as mock_ai:
        yield mock_ai

# --------------------------
# Helper Functions
# --------------------------


def mock_ai_client_response(response):
    """
    Helper function to create a mock ai_client that returns the specified response.
    """
    mock = Mock()
    mock.return_value = response
    return mock

# --------------------------
# parse_response Method Tests
# --------------------------


def test_parse_response_valid(display_choices_instance):
    response = "['Option 1', 'Option 2', 'Option 3']"
    expected = ['Option 1', 'Option 2', 'Option 3']
    assert display_choices_instance.parse_response(
        response) == expected, "Should parse valid response correctly"


def test_parse_response_invalid(display_choices_instance):
    response = "Invalid List"
    with pytest.raises(ValueError, match="Failed to get list of choices"):
        display_choices_instance.parse_response(response)

# --------------------------
# display_choices Method Tests
# --------------------------


def test_display_choices_success(display_choices_instance, mock_pick_success):
    items = ['Option 1', 'Option 2']
    mock_pick_success.return_value = ('Option 1', 0)

    selected_option = display_choices_instance.display_choices(
        items, title="Select an option:")
    assert selected_option == 'Option 1', "Should return the selected option"

    mock_pick_success.assert_called_once_with(
        ['Option 1', 'Option 2', '> Try again', '> Exit'],
        "Select an option:",
        indicator='*',
        multiselect=False,
        min_selection_count=1
    )

# --------------------------
# run Method Tests
# --------------------------


def test_run_valid_selection(display_choices_instance, mock_pick_success):
    items = "['Option 1', 'Option 2', 'Option 3']"
    mock_pick_success.return_value = ('Option 2', 1)

    with patch.object(display_choices_instance, 'parse_response', return_value=['Option 1', 'Option 2', 'Option 3']) as mock_parse:
        with patch.object(display_choices_instance, 'display_choices', return_value='Option 2') as mock_display:
            selected = display_choices_instance.run(items)
            assert selected == 'Option 2', "Should return the selected valid option"
            mock_parse.assert_called_once_with(items)
            mock_display.assert_called_once_with(
                items=['Option 1', 'Option 2', 'Option 3'])


def test_run_invalid_selection(display_choices_instance, mock_pick_success):
    items = "['Option 1', 'Option 2']"
    mock_pick_success.return_value = ('', None)

    with patch.object(display_choices_instance, 'parse_response', return_value=['Option 1', 'Option 2']) as mock_parse:
        with patch.object(display_choices_instance, 'display_choices', return_value='') as mock_display:
            selected = display_choices_instance.run(items)
            assert selected == '', "Should return empty string for invalid selection"
            mock_parse.assert_called_once_with(items)
            mock_display.assert_called_once_with(
                items=['Option 1', 'Option 2'])

# --------------------------
# render_choices_with_try_again Method Tests
# --------------------------


def test_render_choices_with_try_again_success(display_choices_instance, mock_pick_success):
    prompt = "Choose an action:"
    ai_response = "['Option A', 'Option B']"
    expected_choice = 'Option A'

    mock_ai = mock_ai_client_response(ai_response)

    mock_pick_success.side_effect = [
        ('> Try again', None),  # First iteration: user chooses to try again
        (expected_choice, 0)     # Second iteration: user selects a valid option
    ]

    selected = display_choices_instance.render_choices_with_try_again(
        prompt, mock_ai)

    # Then
    assert selected == expected_choice, "Should return the valid selected option after retry"
    assert mock_ai.call_count == 2
    mock_ai.assert_any_call(prompt)


def test_render_choices_with_try_again_exit(display_choices_instance, mock_pick_exit):
    prompt = "Choose an action:"
    ai_response = "['Option A', 'Option B']"

    mock_ai = mock_ai_client_response(ai_response)

    with pytest.raises(Exception, match="User exited"):
        display_choices_instance.render_choices_with_try_again(prompt, mock_ai)

    # Then
    mock_ai.assert_called_once_with(prompt)


def test_render_choices_with_try_again_no_retry(display_choices_instance, mock_pick_success):
    prompt = "Choose an action:"
    ai_response = "['Option X', 'Option Y']"
    expected_choice = 'Option Y'

    mock_ai = mock_ai_client_response(ai_response)

    mock_pick_success.return_value = (expected_choice, 1)

    selected = display_choices_instance.render_choices_with_try_again(prompt, mock_ai)

    # Then
    assert selected == expected_choice, "Should return the selected option without retrying"
    mock_ai.assert_called_once_with(prompt)

# --------------------------
# Integration Tests
# --------------------------


def test_full_flow_success(display_choices_instance, mock_pick_success):
    """
    Integration test for the full flow of render_choices_with_try_again method.
    """
    prompt = "Select an action:"
    ai_response = "['Action 1', 'Action 2']"
    selected_option = 'Action 1'

    mock_ai = mock_ai_client_response(ai_response)

    # User selects 'Action 1' on the first try
    mock_pick_success.return_value = (selected_option, 0)

    choice = display_choices_instance.render_choices_with_try_again(prompt, mock_ai)
    assert choice == selected_option, "Should successfully return the selected action"

    # Then
    mock_ai.assert_called_once_with(prompt)


def test_full_flow_multiple_retries(display_choices_instance, mock_pick_success):
    """
    Integration test where the user retries multiple times before making a valid selection.
    """
    prompt = "Select an action:"
    ai_response = "['Action A', 'Action B']"
    selected_option = 'Action B'

    mock_ai = mock_ai_client_response(ai_response)

    mock_pick_success.side_effect = [
        ("> Try again", None),  # First iteration: user chooses to try again
        ("> Try again", None),  # Second iteration: user chooses to try again
        (selected_option, 1)  # Third iteration: user selects a valid option
    ]

    choice = display_choices_instance.render_choices_with_try_again(prompt, mock_ai)
    assert choice == selected_option, "Should return the selected action after multiple retries"

    # Then
    assert mock_ai.call_count == 3
    mock_ai.assert_called_with(prompt)

# --------------------------
# Additional Edge Case Tests
# --------------------------


def test_display_choices_empty_list(display_choices_instance, mock_pick_success):
    items = []
    mock_pick_success.return_value = ('> Exit', None)

    with pytest.raises(ValueError, match="\n\nFailed to get list of choices, did you stage your changes?"):
        display_choices_instance.run(items)


def test_run_with_empty_response(display_choices_instance, mock_pick_success):
    items = ""
    mock_pick_success.return_value = ('> Exit', None)

    with patch.object(display_choices_instance, 'parse_response', side_effect=ValueError("Failed to parse")):
        with pytest.raises(ValueError, match="Failed to parse"):
            display_choices_instance.run(items)
