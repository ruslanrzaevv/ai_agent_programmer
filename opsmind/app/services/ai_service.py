from __future__ import annotations
import re
from google.genai import types
from google import genai
from google.genai.errors import ServerError
from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.models.models import ExplainMode, Incident, LogEntry

logger = get_logger("ai")

_client = None


def get_client():
    global _client

    if _client is None:
        _client = OpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
    return _client



EXPLAIN_SYSTEM_PROMPTS = {
    ExplainMode.JUNIOR: """You are a patient senior developer explaining an incident to a junior developer.
Use simple language. Explain WHAT happened step by step. Mention which files, containers, or services are involved.
Suggest what to Google or learn. Be encouraging. Keep it under 300 words.""",

    ExplainMode.SENIOR: """You are a staff engineer doing a post-mortem analysis.
Be concise and technical. Include: root cause, blast radius, affected components, stack trace analysis.
Suggest precise fix steps and prevention measures. Use technical terms freely. Under 400 words.""",

    ExplainMode.CEO: """You are a CTO briefing a non-technical CEO.
Avoid all technical jargon. Use business impact language only.
Format EXACTLY:
- What happened: [1 sentence, plain English]
- Duration: [X minutes]
- Business impact: [revenue loss, users affected, SLA breach]
- Root cause: [1 simple analogy]
- Resolution: [1 sentence]
- Prevention: [1 sentence]
Keep it under 150 words.""",
}


async def _generate(prompt: str, system: str) -> str:
    import asyncio

    client = get_client()
    loop = asyncio.get_running_loop()

    response = await loop.run_in_executor(
        None,
        lambda: client.chat.completions.create(
            model="openai/gpt-oss-20b:free",
            messages=[
                {
                    "role": "system",
                    "content": system,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )
    )

    return response.choices[0].message.content
    
class AIService:    
    async def explain_incident(
        self,
        incident: Incident,
        logs: list[LogEntry],
        mode: ExplainMode,
        orbit_context=None,
    ) -> str:
        orbit_context = orbit_context or {}
        
        log_sample = "\n".join(
            f"[{e.timestamp.isoformat()}] [{e.level.upper()}] {e.container_name or ''}: {e.message}"
            for e in logs[:50]
        )
        root_cause = self.extract_root_exception(logs)
        
        logger.warning(
            "AI_PROMPT",
            root_cause=root_cause,
        )
        user_prompt = f"""
        Incident Title: {incident.title}

        ROOT EXCEPTIONS:
        {root_cause}

        ORBIT ANALYSIS:

        Root Component:
        {orbit_context.get("root_component")}

        Affected Services:
        {orbit_context.get("affected_services")}

        Affected Files:
        {orbit_context.get("affected_files")}

        Risk Score:
        {orbit_context.get("risk_score")}

        FULL LOGS:

        {log_sample}
        Timeline summary:
        {self._timeline_summary(incident)}

        Determine the exact root cause.
        Focus on exception names.
        Do not describe generic Internal Server Errors.
        """
        return await _generate(user_prompt, EXPLAIN_SYSTEM_PROMPTS[mode])
    
    
    def extract_root_exception(
        self,
        logs: list[LogEntry],
    ) -> str:

        priority_patterns = [
            r"DoesNotExist",
            r"AttributeError",
            r"TypeError",
            r"ValueError",
            r"KeyError",
            r"IndexError",
            r"RuntimeError",
            r"Exception",   
            r"Traceback",
        ]

        for pattern in priority_patterns:
            for log in reversed(logs):
                if re.search(pattern, log.message, re.IGNORECASE):
                    return log.message.strip()

        return "Unknown"
    

    async def explain_all_modes(
        self, incident: Incident, logs: list[LogEntry]
    ) -> dict[str, str]:
        orbit_context = {
            "root_component": incident.orbit_root_cause,
            "affected_files": incident.orbit_affected_files,
            "affected_services": incident.orbit_affected_services,
            "risk_score": incident.orbit_risk_score,
        }
        results = {}
        for mode in ExplainMode:
            try:
                results[mode.value] = await self.explain_incident(incident, logs, mode, orbit_context,)
            except Exception as e:
                logger.error("ai_explain_failed", mode=mode.value, error=str(e))
                results[mode.value] = f"AI analysis unavailable: {e}"
        return results


    async def suggest_fix(self, incident: Incident, logs: list[LogEntry], orbit_context=None) -> dict[str, str]:
        orbit_context = orbit_context or {}
        log_sample = "\n".join(
            f"[{e.level.upper()}] {e.container_name}: {e.message}"
            for e in logs[:30]
        )
        system = """You are a DevOps expert. Given an incident, produce:
            1. A concise fix description (under 200 words)
            2. An optional executable fix script (bash or docker commands only).

            Respond in this EXACT format:
            DESCRIPTION:
            <your fix description>

            SCRIPT:
            <bash script or "N/A" if not applicable>"""
            
        orbit_text = f"""
        Root Cause:
        {orbit_context.get("root_component")}

        Affected Services:
        {orbit_context.get("affected_services")}

        Affected Files:
        {orbit_context.get("affected_files")}

        Risk Score:
        {orbit_context.get("risk_score")}
        """

        prompt = f"""
        Incident: {incident.title}
        Severity: {incident.severity}

        {orbit_text}

        Logs:

        {log_sample}
        """

        text = await _generate(
            prompt,
            system,
        )

        description, script = "", ""
        if "DESCRIPTION:" in text and "SCRIPT:" in text:
            parts = text.split("SCRIPT:")
            description = parts[0].replace("DESCRIPTION:", "").strip()
            script_raw = parts[1].strip()
            script = "" if script_raw == "N/A" else script_raw
        else:
            description = text

        return {"description": description, "script": script}


    async def ask(
        self,
        question: str,
        incident: Incident | None = None,
        context_logs: list[LogEntry] | None = None,
    ) -> str:
        context = ""
        if incident:
            context = f"Incident context: {incident.title} ({incident.severity})\n"
            context += f"Status: {incident.status}\n"
            context += f"AI analysis: {incident.ai_explanation_senior or 'not yet available'}\n\n"
        if context_logs:
            context += "Recent logs:\n" + "\n".join(
                f"[{e.level}] {e.message}" for e in context_logs[:20]
            )
        system = "You are an expert DevOps assistant for the OpsMind monitoring platform. Answer clearly and concisely."
        return await _generate(f"{context}\n\nQuestion: {question}", system)


    @staticmethod
    def _duration(incident: Incident) -> str:
        end = incident.resolved_at or incident.updated_at
        delta = end - incident.started_at
        minutes = int(delta.total_seconds() / 60)
        return f"{minutes} minutes"


    @staticmethod
    def _timeline_summary(incident: Incident) -> str:
        if not incident.timeline:
            return "No timeline data"
        lines = []
        for point in incident.timeline[:10]:
            lines.append(
                f"  +{point.get('minute', 0)}min: errors={point.get('error_count', 0)} "
                f"cpu={point.get('cpu_percent', '?')}% "
                f"event={point.get('event', '')}"
            )
        return "\n".join(lines)
    
    
    async def generate_code_fix(
    self,
    logs: str,
    source_code: str,
    repo_context: dict,
    ):
        system = """
        You are a Senior Python Software Engineer.

        Analyze:

        1. Error logs
        2. Source code

        Your task:

        - Fix ONLY the bug described in logs.
        - Preserve all existing business logic.
        - Do NOT refactor code.
        - Do NOT rename variables.
        - Do NOT change imports.
        - Do NOT modify unrelated functions.
        - Do NOT change request.user to request.
        - Do NOT change authentication logic.
        - Change the minimum number of lines possible.
        - If you are not 100% sure, return the original code unchanged.

        Return ONLY JSON.

        Format:

        {
            "problem": "",
            "explanation": "",
            "fixed_file": "",
            "commit_message": ""
        }

        IMPORTANT:

        fixed_file MUST contain the COMPLETE corrected source file.

        Return the entire file with ONLY the required bug fix applied.

        No markdown.
        No explanations outside JSON.
        
        AND Use ONLY the provided source code.
        Do not assume any other file version exists.
        
        CRITICAL RULES:

        You are NOT allowed to refactor code.

        You are NOT allowed to improve architecture.

        You are NOT allowed to rename variables, functions, classes, imports, URLs, views, models, serializers, or templates.

        You are NOT allowed to modify unrelated code.

        You must ONLY fix the exact error shown in the logs.

        Preserve all existing business logic.

        Preserve all existing function names.

        Preserve all existing imports unless the error explicitly requires changing them.

        Preserve formatting and structure of the file.

        If the error can be fixed by changing fewer than 10 lines, change fewer than 10 lines.

        Never replace request.user with another variable unless the logs explicitly prove it is incorrect.

        Never rewrite the entire function when a small patch is sufficient.

        Return the COMPLETE file with ONLY the necessary bug fix applied.

        Use ONLY the provided source code.

        Do not invent missing files.

        Do not assume any other version of the code exists.

        Your goal is to create the smallest possible safe patch.
        """        
        prompt = f"""
        Logs:

        {logs}

        Orbit Analysis:

        Root Cause:
        {repo_context.get("orbit_root_cause")}

        Affected Services:
        {repo_context.get("affected_services")}

        Affected Files:
        {repo_context.get("affected_files")}

        Risk Score:
        {repo_context.get("risk_score")}

        Blast Radius:
        {repo_context.get("blast_radius")}

        Source code:

        {source_code}
        """

        text = await _generate(
            prompt,
                system,
         )

        return text
    

    async def review_patch(
    self,
    old_code: str,
    new_code: str,
    ):
            system = """
        You are a Staff Engineer.

        Review proposed code changes.

        Return ONLY JSON.

        {
            "safe": true,
            "reason": ""
        }

        safe=false if patch may break application.
        """

            prompt = f"""
        OLD CODE:

        {old_code}

        NEW CODE:

        {new_code}
        """

            text = await _generate(
                prompt,
                system,
            )

            return text
        
    async def locate_file(
        self,
        logs: str,
        files: list[str],
        orbit_context=None,
    ):
            system = """
        You are a Senior Software Engineer.

        Your task:

        Given:
        1. Error logs
        2. Repository file list

        Find the MOST likely file that contains the bug.

        Return ONLY JSON.

        Format:

        {
            "file": "",
            "confidence": 0.0,
            "reason": ""
        }

        No markdown.
        No explanations outside JSON.
        """

            prompt = f"""
            Logs:

            {logs}

            Orbit Context:

            Root Component:
            {orbit_context}

            Repository files:

            {chr(10).join(files)}
            """

            text = await _generate(
                prompt,
                system,
            )

            return text