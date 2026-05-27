from __future__ import annotations

import anthropic
from app.core.config import settings
from app.core.logging import get_logger
from app.models.models import ExplainMode, Incident, LogEntry

logger = get_logger("ai")

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
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


class AIService:
    def __init__(self) -> None:
        self.client = get_client()


    async def explain_incident(
        self,
        incident: Incident,
        logs: list[LogEntry],
        mode: ExplainMode,
    ) -> str:
        log_sample = "\n".join(
            f"[{e.timestamp.isoformat()}] [{e.level.upper()}] {e.container_name or ''}: {e.message}"
            for e in logs[:50]
        )

        user_prompt = f"""
Incident Title: {incident.title}
Severity: {incident.severity}
Duration: {self._duration(incident)}
Error Count: {incident.error_count}
Affected Containers: {', '.join(incident.affected_containers) or 'unknown'}

Log sample (up to 50 entries):
{log_sample}

Timeline summary:
{self._timeline_summary(incident)}

Explain this incident.
"""

        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=EXPLAIN_SYSTEM_PROMPTS[mode],
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text  # type: ignore[union-attr]

    async def explain_all_modes(
        self, incident: Incident, logs: list[LogEntry]
    ) -> dict[str, str]:
        """Generate all three explanations (called once on incident creation)."""
        results = {}
        for mode in ExplainMode:
            try:
                results[mode.value] = await self.explain_incident(incident, logs, mode)
            except Exception as e:
                logger.error("ai_explain_failed", mode=mode.value, error=str(e))
                results[mode.value] = f"AI analysis unavailable: {e}"
        return results

    # ── Fix suggestion ─────────────────────────────────────────────────────────

    async def suggest_fix(self, incident: Incident, logs: list[LogEntry]) -> dict[str, str]:
        """Returns human-readable fix + optional bash/docker fix script."""
        log_sample = "\n".join(
            f"[{e.level.upper()}] {e.container_name}: {e.message}"
            for e in logs[:30]
        )

        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system="""You are a DevOps expert. Given an incident, produce:
1. A concise fix description (under 200 words)
2. An optional executable fix script (bash or docker commands only).

Respond in this EXACT format:
DESCRIPTION:
<your fix description>

SCRIPT:
<bash script or "N/A" if not applicable>

Be cautious: only suggest scripts that are safe and reversible.""",
            messages=[
                {
                    "role": "user",
                    "content": f"Incident: {incident.title}\nSeverity: {incident.severity}\n\nLogs:\n{log_sample}",
                }
            ],
        )

        text = response.content[0].text  # type: ignore[union-attr]
        description = ""
        script = ""

        if "DESCRIPTION:" in text and "SCRIPT:" in text:
            parts = text.split("SCRIPT:")
            description = parts[0].replace("DESCRIPTION:", "").strip()
            script_raw = parts[1].strip()
            script = "" if script_raw == "N/A" else script_raw
        else:
            description = text

        return {"description": description, "script": script}

    # ── Free-form question about an incident ──────────────────────────────────

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

        response = await self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system="You are an expert DevOps assistant for the OpsMind monitoring platform. Answer clearly and concisely.",
            messages=[
                {"role": "user", "content": f"{context}\n\nQuestion: {question}"},
            ],
        )
        return response.content[0].text  # type: ignore[union-attr]

    # ── Helpers ────────────────────────────────────────────────────────────────

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