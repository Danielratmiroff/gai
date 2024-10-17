from pick import pick
import curses


class DisplayChoices:
    def display_choices(self, items, title="Please select an option:"):
        option, index = pick(items, title, indicator='*',
                             multiselect=False, min_selection_count=1)
        return option

    def run(self, items=None):
        if items is None:
            raise ValueError("Failed to provide choices to display")

        selected_item = self.select_item(items, "Choose a commit message:")
        print(f"\nYou selected: {selected_item}")
