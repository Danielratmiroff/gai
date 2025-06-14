# test_display_choices.py

import pytest
from unittest.mock import patch, Mock, call
import ast

from gai_tool.src.display_choices import DisplayChoices, OPTIONS
from gai_tool.src.prompts import Prompts
from gai_tool.src.utils import create_user_message, create_system_message

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
    with patch('gai_tool.src.display_choices.pick') as mock_pick:
        yield mock_pick


@pytest.fixture
def mock_pick_exit():
    """
    Fixture to mock the pick function selecting the EXIT option.
    """
    with patch('gai_tool.src.display_choices.pick') as mock_pick:
        mock_pick.return_value = (OPTIONS.EXIT.value, None)
        yield mock_pick


@pytest.fixture
def mock_pick_enter_suggestion():
    """
    Fixture to mock the pick function selecting the ENTER_A_SUGGESTION option.
    """
    with patch('gai_tool.src.display_choices.pick') as mock_pick:
        mock_pick.return_value = (OPTIONS.ENTER_A_SUGGESTION.value, None)
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
def test_parse_reasoning_response_valid_json(display_choices_instance):
    REASONING_RESPONSE = 'changes:\n\n1. **Option `1`**: Add parameter.\n2. **Option `2`**: "📄" content tags.\n3. **Option `3`**: Describe handling.\n\n```json\n["Option 1", \n "Option 2", \n "Option 3"]\n```'
    response = REASONING_RESPONSE

    expected = ['Option 1', 'Option 2', 'Option 3']
    assert display_choices_instance.parse_response(
        response) == expected, "Should parse valid response correctly"


def test_parse_reasoning_response_valid(display_choices_instance):
    REASONING_RESPONSE = '<think>\nAlright,\n\nFirst, I\'m a dummy reasoning {self.dummy}, so that\'s straightforward</think>\n\n["Option 1", "Option 2", "Option 3"]'
    response = REASONING_RESPONSE

    expected = ['Option 1', 'Option 2', 'Option 3']
    assert display_choices_instance.parse_response(
        response) == expected, "Should parse valid response correctly"


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
        ['Option 1', 'Option 2', OPTIONS.ENTER_A_SUGGESTION.value, OPTIONS.TRY_AGAIN.value, OPTIONS.EXIT.value],
        "Select an option:",
        indicator='*',
        multiselect=False,
        min_selection_count=1
    )


def test_display_choices_includes_enter_suggestion_option(display_choices_instance, mock_pick_success):
    """Test that the ENTER_A_SUGGESTION option is included in display choices."""
    items = ['Option 1', 'Option 2']
    mock_pick_success.return_value = (OPTIONS.ENTER_A_SUGGESTION.value, 2)

    selected_option = display_choices_instance.display_choices(items)
    assert selected_option == OPTIONS.ENTER_A_SUGGESTION.value, "Should return the ENTER_A_SUGGESTION option"

    expected_items = ['Option 1', 'Option 2', OPTIONS.ENTER_A_SUGGESTION.value,
                      OPTIONS.TRY_AGAIN.value, OPTIONS.EXIT.value]
    mock_pick_success.assert_called_once_with(
        expected_items,
        "Please select an option:",
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
        (OPTIONS.TRY_AGAIN.value, None),  # First iteration: user chooses to try again
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
        ),
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt),
                create_system_message(ai_response),
                create_user_message("Please try again.")
            ],
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
    )


# --------------------------
# Enter a Suggestion Tests
# --------------------------


def test_render_choices_with_enter_suggestion_basic_flow(display_choices_instance, mock_pick_success):
    """Test basic flow when user selects 'Enter a suggestion' option."""
    sys_prompt = "You are an assistant"
    prompt = "user message"
    ai_response = "['Option A', 'Option B']"
    user_suggestion = "Please add option C"
    expected_choice = 'Option C'
    ai_response_after_suggestion = "['Option A', 'Option B', 'Option C']"

    mock_ai = mock_ai_client_response(ai_response)
    mock_ai.side_effect = [ai_response, ai_response_after_suggestion]

    mock_pick_success.side_effect = [
        (OPTIONS.ENTER_A_SUGGESTION.value, None),  # First iteration: user chooses to enter suggestion
        (expected_choice, 2)                       # Second iteration: user selects the new option
    ]

    with patch.object(Prompts, 'build_enter_a_suggestion_prompt', return_value="Please try again while addressing user concerns.") as mock_suggestion_prompt:
        with patch('builtins.input', return_value=user_suggestion) as mock_input:
            selected = display_choices_instance.render_choices_with_try_again(
                user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
            )

    # Assertions
    assert selected == expected_choice, "Should return the selected option after suggestion"
    assert mock_ai.call_count == 2
    mock_input.assert_called_once_with("\nPlease enter your suggestion: ")
    mock_suggestion_prompt.assert_called_once()

    expected_calls = [
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt)
            ],
        ),
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt),
                create_system_message(ai_response),
                create_user_message(
                    "Please try again while addressing user concerns.\nUser suggestion: Please add option C")
            ],
        )
    ]

    mock_ai.assert_has_calls(expected_calls, any_order=False)


def test_render_choices_with_enter_suggestion_then_exit(display_choices_instance, mock_pick_success):
    """Test flow when user enters suggestion then chooses to exit."""
    sys_prompt = "You are an assistant"
    prompt = "user message"
    ai_response = "['Option A', 'Option B']"
    user_suggestion = "Add option C"
    ai_response_after_suggestion = "['Option A', 'Option B', 'Option C']"

    mock_ai = mock_ai_client_response(ai_response)
    mock_ai.side_effect = [ai_response, ai_response_after_suggestion]

    mock_pick_success.side_effect = [
        (OPTIONS.ENTER_A_SUGGESTION.value, None),  # First iteration: user chooses to enter suggestion
        (OPTIONS.EXIT.value, None)                 # Second iteration: user chooses to exit
    ]

    with patch.object(Prompts, 'build_enter_a_suggestion_prompt', return_value="Please try again while addressing user concerns."):
        with patch('builtins.input', return_value=user_suggestion):
            with pytest.raises(Exception, match="User exited"):
                display_choices_instance.render_choices_with_try_again(
                    user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
                )

    assert mock_ai.call_count == 2


def test_render_choices_with_multiple_suggestions(display_choices_instance, mock_pick_success):
    """Test flow when user enters multiple suggestions before making a final choice."""
    sys_prompt = "You are an assistant"
    prompt = "user message"
    ai_response = "['Option A', 'Option B']"
    first_suggestion = "Add option C"
    second_suggestion = "Make option C more specific"
    final_choice = 'Option C Specific'

    ai_responses = [
        ai_response,
        "['Option A', 'Option B', 'Option C']",
        "['Option A', 'Option B', 'Option C Specific']"
    ]

    mock_ai = Mock()
    mock_ai.side_effect = ai_responses

    mock_pick_success.side_effect = [
        (OPTIONS.ENTER_A_SUGGESTION.value, None),  # First: enter suggestion
        (OPTIONS.ENTER_A_SUGGESTION.value, None),  # Second: enter another suggestion
        (final_choice, 2)                          # Third: select final option
    ]

    with patch.object(Prompts, 'build_enter_a_suggestion_prompt', return_value="Please try again while addressing user concerns."):
        with patch('builtins.input', side_effect=[first_suggestion, second_suggestion]):
            selected = display_choices_instance.render_choices_with_try_again(
                user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
            )

    assert selected == final_choice, "Should return the final selected option after multiple suggestions"
    assert mock_ai.call_count == 3


def test_render_choices_with_empty_suggestion(display_choices_instance, mock_pick_success):
    """Test flow when user enters an empty suggestion."""
    sys_prompt = "You are an assistant"
    prompt = "user message"
    ai_response = "['Option A', 'Option B']"
    empty_suggestion = ""
    expected_choice = 'Option A'

    mock_ai = mock_ai_client_response(ai_response)
    mock_ai.side_effect = [ai_response, ai_response]  # Same response after empty suggestion

    mock_pick_success.side_effect = [
        (OPTIONS.ENTER_A_SUGGESTION.value, None),  # First: enter suggestion
        (expected_choice, 0)                       # Second: select option
    ]

    with patch.object(Prompts, 'build_enter_a_suggestion_prompt', return_value="Please try again while addressing user concerns."):
        with patch('builtins.input', return_value=empty_suggestion):
            selected = display_choices_instance.render_choices_with_try_again(
                user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
            )

    assert selected == expected_choice, "Should handle empty suggestion gracefully"
    assert mock_ai.call_count == 2


def test_render_choices_with_suggestion_and_try_again_mixed(display_choices_instance, mock_pick_success):
    """Test flow with mixed usage of suggestion and try again options."""
    sys_prompt = "You are an assistant"
    prompt = "user message"
    ai_response = "['Option A', 'Option B']"
    user_suggestion = "Add option C"
    final_choice = 'Option C'

    ai_responses = [
        ai_response,                           # Initial response
        "['Option A', 'Option B', 'Option C']",  # After suggestion
        "['Option A', 'Option B', 'Option C']"  # After try again
    ]

    mock_ai = Mock()
    mock_ai.side_effect = ai_responses

    mock_pick_success.side_effect = [
        (OPTIONS.ENTER_A_SUGGESTION.value, None),  # First: enter suggestion
        (OPTIONS.TRY_AGAIN.value, None),           # Second: try again
        (final_choice, 2)                          # Third: select final option
    ]

    with patch.object(Prompts, 'build_enter_a_suggestion_prompt', return_value="Please address user concerns."):
        with patch.object(Prompts, 'build_try_again_prompt', return_value="Please try again."):
            with patch('builtins.input', return_value=user_suggestion):
                selected = display_choices_instance.render_choices_with_try_again(
                    user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
                )

    assert selected == final_choice, "Should handle mixed suggestion and try again flow"
    assert mock_ai.call_count == 3

    expected_calls = [
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt)
            ],
        ),
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt),
                create_system_message(ai_response),
                create_user_message("Please address user concerns.\nUser suggestion: Add option C")
            ],
        ),
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt),
                create_system_message(ai_response),
                create_user_message("Please address user concerns.\nUser suggestion: Add option C"),
                create_system_message("['Option A', 'Option B', 'Option C']"),
                create_user_message("Please try again.")
            ],
        )
    ]

    mock_ai.assert_has_calls(expected_calls, any_order=False)


def test_render_choices_suggestion_prompt_building(display_choices_instance, mock_pick_success):
    """Test that the suggestion prompt is built correctly with user input."""
    sys_prompt = "You are an assistant"
    prompt = "user message"
    ai_response = "['Option A', 'Option B']"
    user_suggestion = "My specific suggestion text"
    expected_choice = 'Option A'

    mock_ai = mock_ai_client_response(ai_response)
    mock_ai.side_effect = [ai_response, ai_response]

    mock_pick_success.side_effect = [
        (OPTIONS.ENTER_A_SUGGESTION.value, None),
        (expected_choice, 0)
    ]

    suggestion_prompt = "Base suggestion prompt"

    with patch.object(Prompts, 'build_enter_a_suggestion_prompt', return_value=suggestion_prompt) as mock_suggestion_prompt:
        with patch('builtins.input', return_value=user_suggestion) as mock_input:
            selected = display_choices_instance.render_choices_with_try_again(
                user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
            )

    # Verify the final prompt includes both the base prompt and user suggestion
    expected_final_prompt = f"{suggestion_prompt}\nUser suggestion: {user_suggestion}"

    final_call_args = mock_ai.call_args_list[1]
    final_user_message = final_call_args[1]['user_message'][-1]['content']

    assert final_user_message == expected_final_prompt, "Should combine suggestion prompt with user input"
    mock_suggestion_prompt.assert_called_once()
    mock_input.assert_called_once_with("\nPlease enter your suggestion: ")


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
        (OPTIONS.TRY_AGAIN.value, None),  # First iteration: user chooses to try again
        (OPTIONS.TRY_AGAIN.value, None),  # Second iteration: user chooses to try again
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
        ),
        call(
            user_message=[
                create_system_message(sys_prompt),
                create_user_message(prompt),
                create_system_message(ai_response),
                create_user_message("Please try again.")
            ],
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
        )
    ]

    mock_ai.assert_has_calls(expected_calls, any_order=False)


def test_full_flow_suggestion_integration(display_choices_instance, mock_pick_success):
    """
    Integration test for the complete suggestion flow.
    """
    sys_prompt = "You are an assistant"
    prompt = "Select an action:"
    ai_response = "['Action A', 'Action B']"
    user_suggestion = "Please add Action C which does XYZ"
    ai_response_after_suggestion = "['Action A', 'Action B', 'Action C']"
    selected_option = 'Action C'

    mock_ai = Mock()
    mock_ai.side_effect = [ai_response, ai_response_after_suggestion]

    mock_pick_success.side_effect = [
        (OPTIONS.ENTER_A_SUGGESTION.value, None),  # First: enter suggestion
        (selected_option, 2)                       # Second: select the new option
    ]

    with patch.object(Prompts, 'build_enter_a_suggestion_prompt', return_value="Please address user concerns."):
        with patch('builtins.input', return_value=user_suggestion):
            selected = display_choices_instance.render_choices_with_try_again(
                user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
            )

    assert selected == selected_option, "Should successfully handle complete suggestion flow"
    assert mock_ai.call_count == 2


# --------------------------
# Additional Edge Case Tests
# --------------------------


def test_display_choices_empty_list(display_choices_instance, mock_pick_success):
    items = []
    mock_pick_success.return_value = (OPTIONS.EXIT.value, None)

    with pytest.raises(ValueError):
        display_choices_instance.run(items)


def test_run_with_empty_response(display_choices_instance, mock_pick_success):
    items = ""
    mock_pick_success.return_value = (OPTIONS.EXIT.value, None)

    with patch.object(display_choices_instance, 'parse_response', side_effect=ValueError("Failed to parse")):
        with pytest.raises(ValueError, match="Failed to parse"):
            display_choices_instance.run(items)


def test_enter_suggestion_option_in_display_choices_list(display_choices_instance):
    """Test that ENTER_A_SUGGESTION option is properly included in the choices list."""
    items = ['Option 1', 'Option 2']

    with patch('gai_tool.src.display_choices.pick') as mock_pick:
        mock_pick.return_value = ('Option 1', 0)
        display_choices_instance.display_choices(items)

        # Verify that ENTER_A_SUGGESTION is in the list passed to pick
        call_args = mock_pick.call_args[0][0]  # First positional argument (items list)
        assert OPTIONS.ENTER_A_SUGGESTION.value in call_args, "ENTER_A_SUGGESTION should be in the choices list"
        assert OPTIONS.TRY_AGAIN.value in call_args, "TRY_AGAIN should be in the choices list"
        assert OPTIONS.EXIT.value in call_args, "EXIT should be in the choices list"


def test_suggestion_with_special_characters(display_choices_instance, mock_pick_success):
    """Test handling of user suggestions with special characters."""
    sys_prompt = "You are an assistant"
    prompt = "user message"
    ai_response = "['Option A', 'Option B']"
    user_suggestion = "Add option with special chars: !@#$%^&*(){}[]|\\:;\"'<>?,./"
    expected_choice = 'Option A'

    mock_ai = mock_ai_client_response(ai_response)
    mock_ai.side_effect = [ai_response, ai_response]

    mock_pick_success.side_effect = [
        (OPTIONS.ENTER_A_SUGGESTION.value, None),
        (expected_choice, 0)
    ]

    with patch.object(Prompts, 'build_enter_a_suggestion_prompt', return_value="Base prompt"):
        with patch('builtins.input', return_value=user_suggestion):
            selected = display_choices_instance.render_choices_with_try_again(
                user_msg=prompt, ai_client=mock_ai, sys_prompt=sys_prompt
            )

    assert selected == expected_choice, "Should handle special characters in suggestions"

    # Verify the suggestion was properly included in the message
    final_call_args = mock_ai.call_args_list[1]
    final_user_message = final_call_args[1]['user_message'][-1]['content']
    assert user_suggestion in final_user_message, "Special characters should be preserved in suggestion"
