import ast
from typing import Dict
from pick import pick

OPTIONS: Dict[str, str] = {
    "TRY_AGAIN": "> Try again",
    "EXIT": "> Exit"
}


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

        option, _ = pick(items_refined, title, indicator='*',
                         multiselect=False, min_selection_count=1)
        return option

    def run(self, items: list) -> str:
        selected_item = None
        choices = self.parse_response(items)

        selected_item = self.display_choices(
            choices, "Choose a commit message:")

        print(f"\nYou selected: {selected_item}")
        return selected_item
