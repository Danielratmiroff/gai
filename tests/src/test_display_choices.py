# test_display_choices.py

import pytest
from unittest.mock import patch, Mock, call
import ast

from gai.src.display_choices import DisplayChoices, OPTIONS  # Import OPTIONS
from gai.src.prompts import Prompts
from gai.src.utils import create_user_message, create_system_message  # Import added

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
        mock_pick.return_value = (OPTIONS["EXIT"], None)
        yield mock_pick


# Removed the mock_ai_client fixture as ai_client is passed directly in tests


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
    with pytest.raises(ValueError):
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
        ['Option 1', 'Option 2', OPTIONS["TRY_AGAIN"], OPTIONS["EXIT"]],
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
    sys_prompt = "You are an assistant"
    prompt = "user message"
    ai_response = "['Option A', 'Option B']"
    expected_choice = 'Option A'

    mock_ai = mock_ai_client_response(ai_response)

    mock_pick_success.side_effect = [
        (OPTIONS["TRY_AGAIN"], None),  # First iteration: user chooses to try again
        (expected_choice, 0)            # Second iteration: user selects a valid option
    ]

    with patch.object(Prompts, 'build_try_again_prompt', return_value="Please try again.") as mock_try_again:
        selected = display_choices_instance.render_choices_with_try_again(
            user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt)

    # Then
    assert selected == expected_choice, "Should return the valid selected option after retry"
    assert mock_ai.call_count == 2

    expected_calls = [
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt)
            ],
            system_prompt=sys_prompt
        ),
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt),
                create_system_message(ai_response),
                create_user_message("Please try again.")
            ],
            system_prompt=sys_prompt
        )
    ]

    mock_ai.assert_has_calls(expected_calls, any_order=False)


def test_render_choices_with_try_again_exit(display_choices_instance, mock_pick_exit):
    sys_prompt = "You are an assistant"
    prompt = "user message"
    ai_response = "['Option A', 'Option B']"

    mock_ai = mock_ai_client_response(ai_response)

    with patch.object(Prompts, 'build_try_again_prompt', return_value="Please try again."):
        with pytest.raises(Exception, match="User exited"):
            display_choices_instance.render_choices_with_try_again(
                user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
            )

    # Then
    expected_call = call(
        user_message=[
            create_system_message(sys_prompt),
            create_user_message(prompt)
        ],
        system_prompt=sys_prompt
    )

    mock_ai.assert_has_calls([expected_call], any_order=False)


def test_render_choices_with_try_again_no_retry(display_choices_instance, mock_pick_success):
    sys_prompt = "You are an assistant"
    prompt = "user message"
    ai_response = "['Option X', 'Option Y']"
    expected_choice = 'Option Y'

    mock_ai = mock_ai_client_response(ai_response)

    mock_pick_success.return_value = (expected_choice, 1)

    with patch.object(Prompts, 'build_try_again_prompt', return_value="Please try again."):
        selected = display_choices_instance.render_choices_with_try_again(
            user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
        )

    # Then
    assert selected == expected_choice, "Should return the selected option without retrying"
    mock_ai.assert_called_once_with(
        user_message=[
            create_system_message(sys_prompt),
            create_user_message(prompt)
        ],
        system_prompt=sys_prompt
    )


# --------------------------
# Integration Tests
# --------------------------


def test_full_flow_success(display_choices_instance, mock_pick_success):
    """
    Integration test for the full flow of render_choices_with_try_again method.
    """
    sys_prompt = "You are an assistant"
    prompt = "Select an action:"
    ai_response = "['Action 1', 'Action 2']"
    selected_option = 'Action 1'

    mock_ai = mock_ai_client_response(ai_response)

    # User selects 'Action 1' on the first try
    mock_pick_success.return_value = (selected_option, 0)

    selected = display_choices_instance.render_choices_with_try_again(
        user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
    )

    assert selected == selected_option, "Should successfully return the selected action"

    # Then
    expected_call = call(
        user_message=[
            create_system_message(sys_prompt),
            create_user_message(prompt)
        ],
        system_prompt=sys_prompt
    )

    mock_ai.assert_has_calls([expected_call], any_order=False)


def test_full_flow_multiple_retries(display_choices_instance, mock_pick_success):
    """
    Integration test where the user retries multiple times before making a valid selection.
    """
    sys_prompt = "You are an assistant"
    prompt = "Select an action:"
    ai_response = "['Action A', 'Action B']"
    selected_option = 'Action B'

    mock_ai = mock_ai_client_response(ai_response)

    mock_pick_success.side_effect = [
        (OPTIONS["TRY_AGAIN"], None),  # First iteration: user chooses to try again
        (OPTIONS["TRY_AGAIN"], None),  # Second iteration: user chooses to try again
        (selected_option, 1)            # Third iteration: user selects a valid option
    ]

    with patch.object(Prompts, 'build_try_again_prompt', return_value="Please try again."):
        choice = display_choices_instance.render_choices_with_try_again(
            user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
        )

    assert choice == selected_option, "Should return the selected action after multiple retries"

    # Then
    assert mock_ai.call_count == 3

    # Define the exact expected messages
    expected_calls = [
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt)
            ],
            system_prompt=sys_prompt
        ),
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt),
                create_system_message(ai_response),
                create_user_message("Please try again.")
            ],
            system_prompt=sys_prompt
        ),
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt),
                create_system_message(ai_response),
                create_user_message("Please try again."),
                create_system_message(ai_response),
                create_user_message("Please try again.")
            ],
            system_prompt=sys_prompt
        )
    ]

    mock_ai.assert_has_calls(expected_calls, any_order=False)


# --------------------------
# Additional Edge Case Tests
# --------------------------


def test_display_choices_empty_list(display_choices_instance, mock_pick_success):
    items = []
    mock_pick_success.return_value = (OPTIONS["EXIT"], None)

    with pytest.raises(ValueError):
        display_choices_instance.run(items)


def test_run_with_empty_response(display_choices_instance, mock_pick_success):
    items = ""
    mock_pick_success.return_value = (OPTIONS["EXIT"], None)

    with patch.object(display_choices_instance, 'parse_response', side_effect=ValueError("Failed to parse")):
        with pytest.raises(ValueError, match="Failed to parse"):
            display_choices_instance.run(items)
