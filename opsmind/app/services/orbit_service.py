from __future__ import annotations

import subprocess
import re
from typing import Any
from pathlib import Path



ORBIT_PATH = (
    r"C:\Users\ACER-PC\AppData\Local\glab-cli\bin\orbit.exe"
)


class OrbitService:

    def __init__(
        self,
        gitlab_url: str,
        token: str,
        project_id: str,
    ):
        self.gitlab_url = gitlab_url
        self.token = token
        self.project_id = project_id

    def _query(self, sql: str) -> str:

        result = subprocess.run(
            [
                ORBIT_PATH,
                "sql",
                sql,
            ],
            capture_output=True,
            text=True,
        )

        return result.stdout

    async def find_root_cause(
        self,
        logs_text: str,
    ) -> dict[str, Any]:

        affected_files = []
        project_files = []
        keywords = []
        

        file_matches = re.findall(
            r'File "([^"]+)", line (\d+)',
            logs_text,
        )

        project_file = None
        error_line = None


        for file_path, line in reversed(file_matches):

            if (
                "site-packages" not in file_path
                and "python" not in file_path
                and "/usr/local/lib" not in file_path
            ):
                project_file = file_path
                error_line = int(line)
                break
            
        project_files = list(dict.fromkeys(project_files))

        for file_path, _ in file_matches:

            if (
                "site-packages" not in file_path
                and "python" not in file_path
                and "/usr/local/lib" not in file_path
            ):
                project_files.append(file_path)

        project_files = list(
            dict.fromkeys(project_files)
        )

        if project_file:
                normalized = project_file.lstrip("/")
                if normalized.startswith("app/"):
                    normalized = normalized[4:]
                affected_files.append(normalized)

        error_match = re.findall(
            r"([A-Za-z]+Error)",
            logs_text,
        )
        
        root_error = (
            error_match[-1]
            if error_match
            else None
        )

        patterns = [
            r"([a-zA-Z_]+Service)",
            r"([a-zA-Z_]+Collector)",
            r"([a-zA-Z_]+Manager)",
            r"([a-zA-Z_]+Repository)",
            r"([a-zA-Z_]+Controller)",
        ]

        for pattern in patterns:
            keywords.extend(
                re.findall(pattern, logs_text)
            )

        keywords = list(
            dict.fromkeys(keywords)
        )

        for keyword in keywords:

            sql = f"""
            SELECT DISTINCT file_path
            FROM gl_definition
            WHERE name ILIKE '%{keyword}%'
            LIMIT 20
            """

            output = self._query(sql)

            for row in output.splitlines():

                file_path = (
                    row.strip()
                    .replace("|", "")
                )

                if not file_path.endswith(".py"):
                    continue

                if (
                    "site-packages" in file_path
                    or "/usr/local/lib" in file_path
                    or "django/" in file_path
                ):
                    continue

                affected_files.append(
                    file_path
                )

        affected_files = list(
            dict.fromkeys(affected_files)
        )

        files = (
            project_files
            if project_files
            else affected_files
        )
        print("ROOT ERROR =", root_error)
        print("PROJECT FILE =", project_file)
        print("ERROR LINE =", error_line)
        debug = self._query("SELECT DISTINCT file_path FROM gl_definition LIMIT 20")
        print("=== ORBIT INDEX FILES ===")
        print(debug)
        print("=========================")

        return {
            "root_component": (
                root_error
                if root_error
                else (
                    keywords[0]
                    if keywords
                    else None
                )
            ),

            "affected_files": files,

            "affected_services": keywords,

            "error_line": error_line,

            "risk_score": min(
                len(files) * 10,
                100,
            ),
        }        
        
    async def blast_radius(self, file_path: str,):
        file_path = file_path.lstrip("/")
        if file_path.startswith("app/"):
            file_path = file_path[4:]
        
        debug_sql = "SELECT DISTINCT file_path FROM gl_definition LIMIT 20"
        debug_out = self._query(debug_sql)
        print("ORBIT FILES IN DB:", debug_out)

        defs_sql = f"""
        SELECT COUNT(*)
        FROM gl_definition
        WHERE file_path='{file_path}'
        """

        imports_sql = f"""
        SELECT COUNT(*)
        FROM gl_imported_symbol
        WHERE file_path='{file_path}'
        """

        calls_sql = """
        SELECT COUNT(*)
        FROM gl_edge
        WHERE relationship_kind='CALLS'
        """

        defs = self._query(defs_sql)
        imports = self._query(imports_sql)
        calls = self._query(calls_sql)

        def extract(text):
            nums = re.findall(r"\d+", text)
            return int(nums[-1]) if nums else 0

        definitions = extract(defs)
        imports_count = extract(imports)
        calls_count = extract(calls)

        score = min(
            definitions
            + imports_count * 2
            + calls_count,
            100
        )

        return {
            "files": [file_path],
            "services": [],
            "definitions": definitions,
            "imports": imports_count,
            "calls": calls_count,
            "score": score,
        }
            
    async def dependency_tree(self, file_path: str):
        file_path = file_path.lstrip("/")
        if file_path.startswith("app/"):
            file_path = file_path[4:]
        
        sql = f"""
        SELECT
            e.relationship_kind,
            d.file_path as target_file,
            d.name as target_name
        FROM gl_edge e
        JOIN gl_definition d ON e.target_id = d.id
        WHERE e.source_id IN (
            SELECT id FROM gl_definition
            WHERE file_path = '{file_path}'
        )
        AND e.relationship_kind IN (
            'CALLS',
            'IMPORTS',
            'EXTENDS'
        )
        LIMIT 200
        """
        output = self._query(sql)
        return {"graph": output}       
    
        
    async def analyze_incident(
        self,
        logs: str,
    ):
        return await self.find_root_cause(
            logs
        )
        
    async def repository_impact(
    self,
    file_path: str,
    ):
        deps = await self.dependency_tree(
            file_path
        )

        return {
            "file": file_path,
            "graph": deps,
        }
    


    def build_graph(
        self,
        repo_path: str,
    ):
        subprocess.run(
            [
                ORBIT_PATH,
                "index",
                repo_path,
            ],
            check=True,
        )
        


