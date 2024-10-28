import ast
from typing import Dict, List, Callable
from pick import pick

from gai.src.prompts import Prompts
from gai.src.utils import create_user_message


OPTIONS: Dict[str, str] = {
    "START": "start",
    "TRY_AGAIN": "> Try again",
    "EXIT": "> Exit"
}


# TODO: rename this class to avoid cammel case
class DisplayChoices:
    def __init__(self):
        self.history: List[Dict[str, str]] = []

    def parse_response(self, response: str) -> list:
        try:
            result = ast.literal_eval(response)
            if not isinstance(result, list):
                raise ValueError("Response must evaluate to a list")
            return result
        except (ValueError, SyntaxError) as e:
            print(f"Debug - Response that failed parsing: {repr(response)}")  # Show exact string content
            raise ValueError(
                f"\n\nFailed to parse response into list. Error: {str(e)}") from e

    def display_choices(self, items: list, title="Please select an option:"):
        items_refined = items + [OPTIONS["TRY_AGAIN"], OPTIONS["EXIT"]]

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
        choice = OPTIONS["START"]
        messages: List[Dict[str, str]] = [create_user_message(user_msg)]

        # print(f"User message: {messages}")
        response = ai_client(
            user_message=messages,
            system_prompt=sys_prompt
        )

        print(f"Prompt response: {response}")
        choice = self.run(response)

        while choice == OPTIONS["TRY_AGAIN"]:
            try_again_prompt = Prompts().build_try_again_prompt()
            messages.append(create_user_message(try_again_prompt))

            print(f"Try again prompt: {messages}")
            response = ai_client(
                user_message=messages,
                system_prompt=sys_prompt
            )
            print(f"Prompt response: {response}")

            choice = self.run(response)
            print(f"Selection {choice}")

        if choice == OPTIONS["EXIT"]:
            raise Exception("User exited")

        return choice

    def run(self, items: list) -> str:
        selected_item = None
        choices = self.parse_response(items)

        selected_item = self.display_choices(
            items=choices
            # title="Choose an option:"
        )

        print(f"\nYou selected: {selected_item}")
        return selected_item
