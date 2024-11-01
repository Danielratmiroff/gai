COMMITS_MESSAGES = ""


class Prompts:
    def build_ticket_identifier_prompt(self) -> str:
        return """
        <instructions>
            You are a ticket-or-not classifier. Specifically, you will be given a message generated by an engineering assistant.
            Your job is to determine whether or not it contains a ticket number / a ticket identifier meant to track a software requirement request,
            such as Jira tickets. Give your answer with a single word containing the ticket identifier 
            as in: "TICKET-1234" or "None". Note that you MUST not include any other information in your answer
            good example: "TICKET-1234-first-iteration" -> "TICKET-1234"
            good example: "project/feature-branch" -> "None"
            good example: "project/TICKET-1234-second-iteration" -> "TICKET-1234"
            bad example: "TICKET-1234-first-iteration" -> "TICKET-1234-first-iteration"
        </instructions>
        """

    def build_try_again_prompt(self) -> str:
        return """
            Previous attempts weren't satisfactory. Please try again.
            _MUST_ follow the instructions provided as in the first request.
        """

    def build_commit_message_system_prompt(self) -> str:
        return """<instructions>
            You will be provided with git diffs from a local repository.
            Your task is to analyze these diffs thoroughly—including all changes,
            file names, and relevant context—to generate up to three concise and
            meaningful git commit message options that accurately describe the changes made.

            Requirements:

            Analyze All Changes:
            Carefully read every addition, deletion, and modification in the diffs
            Understand the purpose and impact of the changes
            Take note of any patterns or themes across multiple files

            Consider File Names and Paths:
            Use file names and their directory paths to glean additional context
            Recognize if changes are isolated to a specific module, feature, or component

            Generate Human-Meaningful Commit Messages:
            Summarize the essence of the changes in clear and concise language
            Focus on the "what" and "why," not the "how."
            Use the imperative mood (e.g., "Fix issue where...", "Add feature to...", "Update dependency for...").

            Provide Up to Three Options:
            Offer a maximum of three distinct commit message options
            Ensure each option captures different aspects or perspectives if applicable

            Follow Best Practices:
            _MUST_ Keep the commit message summary under 72 characters
            Avoid technical jargon unless it's necessary for clarity
            _MUST_ NOT include irrelevant information or personal comments or opinions

            Formatting:
            _MUST_ Reply the commit messages as an array of messages in the following format: ["Message 1", "Message 2", "Message 3"]
            _MUST_ Do not include any additional text outside the commit messages
            </instructions>
          """

    def build_merge_title_system_prompt(self) -> str:
        return """<instructions>

            You will be provided with a list of git commits from a local branch.
            Your task is to analyze all the changes represented by these commits thoroughly—including code changes,
            commit messages, and any relevant context—to generate up to three concise and
            meaningful pull request title options that accurately summarize the overall changes.

            Requirements:

            Analyze All Changes:
            Read through all the commit messages and, if available, the associated code changes.
            Understand the cumulative purpose and impact of the changes.
            Identify overarching themes or significant modifications that span multiple commits.

            Generate a Human-Understandable and Summarized Pull Request Title:
            Summarize the essence of the combined changes in clear and concise language.
            Focus on the overall purpose and impact of the pull request.
            Use the imperative mood(e.g., "Add user authentication system", "Fix data processing bug").

            Provide Up to Three Options:
            Offer a maximum of three distinct pull request title options.
            Ensure each option captures different aspects or perspectives if applicable.

            Follow Best Practices:
            Keep the pull request title concise, _MUST_ be under 72 characters.
            Avoid technical jargon unless necessary for clarity.
            _MUST_ NOT include irrelevant information or personal comments or opinions

            Formatting:
            Present the pull request titles as an array of messages in the following format: ["Message 1", "Message 2", "Message 3"]
            _MUST_ Do not include any additional text outside the pull request titles.
            </instructions>
          """
