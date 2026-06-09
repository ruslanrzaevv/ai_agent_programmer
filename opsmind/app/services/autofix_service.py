import json
import uuid
import requests
import subprocess

from app.services.ai_service import AIService
from app.services.gitlab_service import GitLabService
from app.workers.monitoring_manager import monitoring_manager
from app.services.gitlab_context_service import GitLabContextService


class AutoFixService:

    def __init__(self):
        self.ai = AIService()

    async def create_fix(
        self,
        incident,
        project,
        logs: str,
    ):  
        print("CREATE FIX STARTED")
        gitlab = GitLabService(
            url=project.gitlab_url,
            token=project.gitlab_token,
            project_id=project.gitlab_project_id,
        )

        files = []

        for item in gitlab.project.repository_tree(
            recursive=True,
            all=True,
        ):
            if item["type"] == "blob":
                files.append(item["path"])

        located = await self.ai.locate_file(
            logs,
            files,
        )
        if located is None:
            return {
                "success": False,
                "message": "Gemini API unavailable",
            }

        print("LOCATED RAW", located)
        located = json.loads(located)

        target_file = located["file"]
        if not target_file:
            raise Exception(
                f"AI could not locate file. Response: {located}"
            )
        source_code = gitlab.get_file(
            target_file,
        )
        
        context = GitLabContextService(
            project
        ).get_repository_context()

        fix = await self.ai.generate_code_fix(
            logs,
            source_code,
            context,
        )
        
        if not fix:
            raise Exception('Gemini API unavailable')

        print("FIX RAW =", fix)
        fix = fix.replace("```json", "")
        fix = fix.replace("```", "")
        fix = fix.strip()
        
        fix = json.loads(fix)
        print("LOCATED RAW", located)
        print("FIX RAW =", fix)
        print("TARGET FILE =", target_file)
        print("OLD CODE =", fix.get("old_code"))
        print("NEW CODE =", fix.get("new_code"))
   

        incident.ai_fix_file = target_file
        incident.ai_fix_old_code = source_code
        incident.ai_fix_new_code = fix["fixed_file"]
        incident.ai_fix_suggestion = fix["explanation"]
        print("CREATE FIX SUCCESS")
        print("FIX KEYS =", fix.keys())
        return {
            "file": target_file,
            "safe": True,
            "commit_message": fix["commit_message"],
        }
        
        
    async def apply_fix(
            self,
            incident,
            project,
        ):
            print("APPLY FIX STARTED")
            gitlab = GitLabService(
                url=project.gitlab_url,
                token=project.gitlab_token,
                project_id=project.gitlab_project_id,
            )

            print("FILE =", incident.ai_fix_file)
            print("CONTENT LENGTH =", len(incident.ai_fix_new_code))

            try:
                gitlab.update_file(
                    branch="main",
                    file_path=incident.ai_fix_file,
                    content=incident.ai_fix_new_code,
                    commit_message="OpsMind AI AutoFix",
                )

                print("COMMIT TO MAIN SUCCESS")

            except Exception as e:
                print("GITLAB ERROR =", e)
                raise

            
            subprocess.run(
                ["git", "restore", "."],
                cwd=r"C:\Users\ACER-PC\Desktop\chetam"
            )

            subprocess.run(
                ["git", "pull", "origin", "main"],
                cwd=r"C:\Users\ACER-PC\Desktop\chetam"
            )
            await monitoring_manager.restart_project(
                str(project.id)
            )
            incident.ai_fix_applied = True
    
            return {
                "success": True,
            }
            