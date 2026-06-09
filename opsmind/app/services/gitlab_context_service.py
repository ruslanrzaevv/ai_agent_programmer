from app.services.gitlab_service import GitLabService


class GitLabContextService:

    def __init__(self, project):
        self.gitlab = GitLabService(
            url=project.gitlab_url,
            token=project.gitlab_token,
            project_id=project.gitlab_project_id,
        )

    def get_repository_context(self):
        commits = self.get_recent_commits()
        files = self.gitlab.list_python_files()

        return {
            "commits": commits,
            "files": files[:100],
        }

    def get_recent_commits(self, limit=10):
        commits = self.gitlab.project.commits.list(
            per_page=limit
        )

        return [
            {
                "id": c.id,
                "title": c.title,
                "author": c.author_name,
            }
            for c in commits
        ]

    def get_recent_merge_requests(self, limit=10):
        mrs = self.gitlab.project.mergerequests.list(
            per_page=limit
        )

        return [
            {
                "iid": mr.iid,
                "title": mr.title,
                "state": mr.state,
            }
            for mr in mrs
        ]