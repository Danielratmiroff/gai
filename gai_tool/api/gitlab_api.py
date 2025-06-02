import os
import gitlab
import subprocess
from typing import Optional, Dict, Any

from gai_tool.src import Merge_requests, ConfigManager, get_app_name


class Gitlab_api():
    def __init__(self):
        self.load_config()
        self.Merge_requests = Merge_requests().get_instance()
        self.gl = self._initialize_gitlab_client()
        self.project = self._get_project()

    def load_config(self):
        config_manager = ConfigManager(get_app_name())
        self.target_branch = config_manager.get_config('target_branch')
        self.assignee_id = config_manager.get_config('assignee_id')

    def _initialize_gitlab_client(self) -> gitlab.Gitlab:
        """Initialize the GitLab client with authentication."""
        api_key = self.get_api_key()
        gitlab_domain = self.Merge_requests.get_remote_url()
        gitlab_url = f"https://{gitlab_domain}"

        return gitlab.Gitlab(gitlab_url, private_token=api_key)

    def _get_project(self):
        """Get the GitLab project object."""
        repo_owner = self.Merge_requests.get_repo_owner_from_remote_url()
        repo_name = self.Merge_requests.get_repo_from_remote_url()
        project_path = f"{repo_owner}/{repo_name}"

        try:
            return self.gl.projects.get(project_path)
        except gitlab.exceptions.GitlabGetError as e:
            raise ValueError(f"Failed to get project {project_path}: {e}")

    def get_api_key(self) -> str:
        """Get the GitLab API key from environment variables."""
        api_key = os.environ.get("GITLAB_PRIVATE_TOKEN")

        if api_key is None:
            raise ValueError(
                "GITLAB_PRIVATE_TOKEN is not set, please set it in your environment variables")

        return api_key

    def get_current_branch(self) -> str:
        """Get the current Git branch name."""
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        return result.stdout.strip()

    def get_existing_merge_request(self, source_branch: str) -> Optional[Dict[str, Any]]:
        """
        Get existing merge request for the current branch.

        Args:
            source_branch: The source branch name

        Returns:
            Dict containing merge request data if found, None otherwise
        """
        try:
            # Get merge requests filtered by source branch and state
            merge_requests = self.project.mergerequests.list(
                source_branch=source_branch,
                state='opened',
                all=True
            )

            if merge_requests:
                # Return the first open merge request as a dict
                mr = merge_requests[0]
                return mr._attrs

            return None

        except gitlab.exceptions.GitlabError as e:
            print(f"Error fetching merge requests: {e}")
            return None

    def update_merge_request(self, mr_iid: int, title: str, description: str) -> None:
        """
        Update an existing merge request.

        Args:
            mr_iid: The internal ID of the merge request
            title: New title for the merge request
            description: New description for the merge request
        """
        try:
            # Get the merge request by internal ID
            mr = self.project.mergerequests.get(mr_iid)

            # Update the merge request
            mr.title = title
            mr.description = description
            mr.remove_source_branch = True
            mr.squash = True

            mr.save()

            print(f"Merge request updated successfully with internal ID: {mr_iid}")

        except gitlab.exceptions.GitlabError as e:
            print(f"Failed to update merge request: {e}")

    def create_merge_request(self, title: str, description: str, target_branch: str = None) -> None:
        """
        Create a new merge request or update existing one.

        Args:
            title: Title for the merge request
            description: Description for the merge request
            target_branch: Target branch for the merge request (overrides config if provided)
        """
        source_branch = self.get_current_branch()
        existing_mr = self.get_existing_merge_request(source_branch)

        # Use provided target_branch or fall back to config
        target_branch_to_use = target_branch if target_branch is not None else self.target_branch

        if existing_mr:
            print(f"A merge request already exists: {existing_mr['web_url']}")
            self.update_merge_request(
                mr_iid=existing_mr['iid'],
                title=title,
                description=description
            )
        else:
            try:
                # Create new merge request
                mr_data = {
                    "source_branch": source_branch,
                    "target_branch": target_branch_to_use,
                    "title": title,
                    "description": description,
                    "remove_source_branch": True,
                    "squash": True
                }

                # Add assignee if configured
                if self.assignee_id:
                    mr_data["assignee_id"] = self.assignee_id

                mr = self.project.mergerequests.create(mr_data)

                print(f"Merge request created successfully with internal ID: {mr.iid}")
                print(f"URL: {mr.web_url}")

            except gitlab.exceptions.GitlabCreateError as e:
                print(f"Failed to create merge request: {e}")
