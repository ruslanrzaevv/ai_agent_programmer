import gitlab
import base64
import time
import subprocess
from pathlib import Path

class GitLabService:

    def __init__(
        self,
        url: str,
        token: str,
        project_id: str,
    ):
        self.gl = gitlab.Gitlab(
            url,
            private_token=token,
        )

        self.project = self.gl.projects.get(
            project_id
        )

    def get_file(self, file_path, branch="main"):
        for attempt in range(3):
            try:
                file = self.project.files.get(
                    file_path=file_path,
                    ref=branch,
                )
                return file.decode().decode()

            except gitlab.exceptions.GitlabGetError as e:
                if e.response_code == 502:
                    time.sleep(2)
                    continue
                raise

        raise Exception(
            "GitLab temporary unavailable"
        )    
    
    def create_branch(
        self,
        branch_name: str,
        source="main",
    ):
        self.project.branches.create({
            "branch": branch_name,
            "ref": source,
        })


    def update_file(
        self,
        branch: str,
        file_path: str,
        content: str,
        commit_message: str,
    ):
        file = self.project.files.get(
            file_path=file_path,
            ref=branch,
        )

        file.content = content

        file.save(
            branch=branch,
            commit_message=commit_message,
        )


    def create_merge_request(
        self,
        source_branch: str,
        target_branch="main",
    ):
        return self.project.mergerequests.create({
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": f"OpsMind AI Fix {source_branch}",
        })
        
        
    def list_python_files(self):
        tree = self.project.repository_tree(
            recursive=True,
            all=True,
        )

        result = []

        for item in tree:

            if item["type"] != "blob":
                continue

            path = item["path"]

            if path.endswith(".py"):
                result.append(path)

        return result
    
    
    def clone_repository(
        self,
        local_path: str,
    ):
        Path(local_path).parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        project = self.project

        repo_url = (
            project.http_url_to_repo
            .replace(
                "https://",
                f"https://oauth2:{self.gl.private_token}@",
            )
        )

        subprocess.run(
            [
                "git",
                "clone",
                repo_url,
                local_path,
            ],
            check=True,
        )


    def pull_repository(
        self,
        local_path: str,
    ):
        subprocess.run(
            [
                "git",
                "-C",
                local_path,
                "pull",
            ],
            check=True,
        )

