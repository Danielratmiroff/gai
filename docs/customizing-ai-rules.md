# Customizing AI Behavior with Rules

The `gai-tool` allows you to customize the behavior of the AI by editing the `gai-rules.md` file. These rules guide the AI in generating commit messages, pull request titles, and merge descriptions, ensuring they align with your project's conventions.

## How It Works

When you run a `gai` command, the tool looks for a `gai-rules.md` file. The content of this file is injected directly into the system prompt sent to the AI.

The tool searches for the rules file in the following order of precedence:

1.  **Project-level**: `.gai/gai-rules.md` in your current project.
2.  **Home-level**: `~/.gai/gai-rules.md` in your home directory.
3.  **Default**: If no file is found, internal default rules are used.

This allows you to set global rules and override them on a per-project basis.

## How to Customize Rules

1.  **Initialize**: If you haven't already, run `gai init` in your project repository. This will create a `.gai/gai-rules.md` file with the default rules.

2.  **Edit**: Open the `gai-rules.md` file and modify its content. You can add, remove, or change the rules to match your workflow. For example, you could enforce conventional commit standards, specify a different language, or require ticket numbers in commit messages.

The AI will use whatever instructions are in this file to shape its output.
