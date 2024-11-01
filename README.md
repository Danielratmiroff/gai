# Gai is an AI-Powered Automation Tool for Git 🚀

![codecov](https://codecov.io/gh/Danielratmiroff/gai/branch/master/graph/badge.svg)
[![PyPI version](https://badge.fury.io/py/gai-tool.svg)](https://badge.fury.io/py/gai-tool)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

command-line application that automates git commit messages and merge requests using AI. 

## ✨ Features

- **Automated Commit Messages**: Generate commit messages based on code diffs.
- **Automated Merge Requests**: Create merge requests with AI-generated titles and descriptions.
- **Multi-Platform Support**: Works with both GitHub and GitLab.
- **Configurable AI Interfaces**: Supports Groq and Hugging Face AI interfaces.

## 📦 Installation

Install gai-tool via pip:

```bash
pip install gai-tool
```

## 🚀 Getting Started

1. **Navigate to your git repository**:

   ```bash
   cd /path/to/your/git/repo
   ```

2. **Set API Tokens as Environment Variables**:

   Ensure you have your AI interface and GitHub/GitLab API tokens set:

   ```bash
   export GROQ_API_KEY='your_groq_api_key'             # If you want to use Groq's API
   export HUGGINGFACE_API_TOKEN='your_hf_api_token'    # If you want to use Hugging Face's API
   export GITHUB_TOKEN='your_github_token'             # If using GitHub
   export GITLAB_TOKEN='your_gitlab_token'             # If using GitLab
   ```

## ⚙️ Configuration

Configuration file is located at `~/.config/gai/config.yaml`. Customize settings like the AI interface, temperature, and target branch.

Example configuration:

```yaml
interface: groq
temperature: 0.7
target_branch: main
```

## 📖 Usage

gai-tool provides two main commands: `commit` and `merge`.

### 📝 Commit Messages

Generate an commit message:

```bash
gai commit
```

Options:

- `-a`, `--all`: Stage all changes before committing.
- `-t`, `--temperature`: Override the temperature specified in the config.
- `-i`, `--interface`: Specify and override the AI client API to use (`groq` or `huggingface`).

**Example**:
```bash
# Simply
gai commit -a
```

```bash
# Or
gai commit -a -t 0.5 -i huggingface
```

This will:

1. Stage all changes.
2. Generate a commit message based on the diffs using the Hugging Face interface with a temperature of 0.5.
3. Commit the changes.

### 🔀 Merge Requests

Create a merge request:

```bash
gai merge
```

Options:

- `[remote]`: Specify the remote git repository (default is `origin`).
- `--push`, `-p`: Push changes to remote before creating a merge request.
- `--target-branch`, `-tb`: Specify the target branch for the merge request (default is `master`).
- `-t`, `--temperature`: Override the temperature specified in the config.
- `-i`, `--interface`: Specify and override the AI client API to use (`groq` or `huggingface`).

**Example**:
```bash
# Simply
gai merge -p
```

```bash
# Or
gai merge origin -p -tb develop -t 0.8 -i groq
```

This will:

1. Push your current branch to the remote repository.
2. Generate a merge request title and description based on your commits.
3. Create a merge request from your current branch to the `develop` branch.

## 🛠 Build Instructions

If you wish to build gai-tool from source:

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/Danielratmiroff/gai.git
   ```

2. **Navigate to the Project Directory**:

   ```bash
   cd gai
   ```

3. **Create a Virtual Environment (Optional but Recommended)**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use venv\Scripts\activate
   ```

4. **Install Build Tools and Dependencies**:

   ```bash
   pip install build
   pip install -r requirements.txt
   ```

5. **Build the Package**:

   ```bash
   python -m build
   ```

   This will generate distribution files in the `dist/` directory.

6. **Install the Built Package**:

   ```bash
   pip install dist/gai_tool-0.1.0-py3-none-any.whl
   ```

## 🤝 Contributing

Contributions are welcome! If you have ideas for improvements or have found bugs, please open an issue or submit a pull request.


## 📄 License

MIT License - [LICENSE](LICENSE).