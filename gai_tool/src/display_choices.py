import ast
from enum import Enum
from typing import Dict, List, Callable
from colorama import Fore, Style
from pick import pick
import re
import ast

from gai_tool.src.prompts import Prompts
from gai_tool.src.utils import create_user_message, create_system_message


class OPTIONS(Enum):
    START = "start"
    TRY_AGAIN = "> Try again"
    ENTER_A_SUGGESTION = "> Enter a suggestion"
    EXIT = "> Exit"


# TODO: rename this class to avoid cammel case
class DisplayChoices:
    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def parse_response(self, response: str) -> list:
        try:
            # Extract content after </think> tag if present
            if "</think>" in response:
                response = response.split("</think>", 1)[1].strip()

            # Only extract JSON block if "```json" is in the response
            if "```json" in response:
                json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)

            # Only extract code block if "```" is in the response
            if "```markdown" in response:
                json_match = re.search(r"```markdown\s*(.*?)\s*```", response, re.DOTALL)
                if json_match:
                    response = json_match.group(1)

            result = ast.literal_eval(response)
            if not isinstance(result, list):
                raise ValueError("Response must evaluate to a list")
            return result

        except (ValueError, SyntaxError) as e:
            print(f"Debug - Response that failed parsing: {repr(response)}")
            raise ValueError(f"\n\nFailed to parse response into list. Error: {str(e)}") from e

    def display_choices(self, items: list, title="Please select an option:"):
        items_refined = items + [OPTIONS.ENTER_A_SUGGESTION.value, OPTIONS.TRY_AGAIN.value,  OPTIONS.EXIT.value]

        option, _ = pick(items_refined,
                         title,
                         indicator='*',
                         multiselect=False,
                         min_selection_count=1)
        return option

    def render_choices_with_try_again(
        self,
        user_msg: str,
        ai_client: Callable[[str, str], str],
        sys_prompt: str
    ) -> str:
        choice = OPTIONS.START

        messages: List[Dict[str, str]] = [
            create_system_message(sys_prompt),
            create_user_message(user_msg)
        ]

        response = ai_client(
            user_message=messages.copy(),
        )

        choice = self.run(response)

        while choice == OPTIONS.TRY_AGAIN.value or choice == OPTIONS.ENTER_A_SUGGESTION.value:
            if choice == OPTIONS.TRY_AGAIN.value:
                try_again_prompt = Prompts().build_try_again_prompt()
                messages.append(create_system_message(response))
                messages.append(create_user_message(try_again_prompt))
            elif choice == OPTIONS.ENTER_A_SUGGESTION.value:
                enter_a_suggestion_prompt = Prompts().build_enter_a_suggestion_prompt()

                # Ask the user for a suggestion
                suggestion = input("\nPlease enter your suggestion: ")
                suggestion_prompt_with_user_suggestion = f"{enter_a_suggestion_prompt}\nUser suggestion: {suggestion}"

                messages.append(create_system_message(response))
                messages.append(create_user_message(suggestion_prompt_with_user_suggestion))

            response = ai_client(
                user_message=messages.copy(),
            )

            choice = self.run(response)

        if choice == OPTIONS.EXIT.value:
            raise Exception("User exited")

        return choice

    def run(self, items: list) -> str:
        selected_item = None
        choices = self.parse_response(items)

        selected_item = self.display_choices(
            items=choices
            # title="Choose an option:"
        )

        print(f"\n{Fore.CYAN}You selected: {selected_item}{Style.RESET_ALL}")
        return selected_item
