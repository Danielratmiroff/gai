import ast
from typing import Dict
from pick import pick

OPTIONS: Dict[str, str] = {
    "TRY_AGAIN": "> Try again",
    "EXIT": "> Exit"
}


# TODO: rename this class to avoid cammel case
class DisplayChoices:
    def __init__(self):
        pass

    def parse_response(self, response: str) -> list:
        try:
            return ast.literal_eval(response)
        except (ValueError, SyntaxError) as e:
            raise ValueError(
                "\n\nFailed to get list of choices, did you stage your changes?") from e

    def display_choices(self, items: list, title="Please select an option:"):
        items_refined = items + [OPTIONS["TRY_AGAIN"], OPTIONS["EXIT"]]

        option, _ = pick(items_refined,
                         title,
                         indicator='*',
                         multiselect=False,
                         min_selection_count=1)
        return option

    def render_choices_with_try_again(self, prompt: str, ai_client: callable) -> str:
        choice = ""

        while choice == OPTIONS["TRY_AGAIN"] or choice == "":
            response = ai_client(prompt)
            print(f"response: {response}")
            choice = self.run(response)
            print(f"selection {choice}")

        if choice == OPTIONS["EXIT"]:
            print("Exiting...")
            return

    def run(self, items: list) -> str:
        selected_item = None
        choices = self.parse_response(items)

        selected_item = self.display_choices(
            items=choices
            # title="Choose an option:"
        )

        print(f"\nYou selected: {selected_item}")
        return selected_item
