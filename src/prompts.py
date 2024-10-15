COMMITS_MESSAGES = ""


class Prompts:
    def build_commit_message_prompt(self, content: str) -> str:
        return f"""Instructions:
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
            Do not include irrelevant information or personal opinions

            Formatting:
            Present the commit messages in a numbered list
            _MUST_ Do not include any additional text outside the commit messages

            Input:
            {content}
          """
