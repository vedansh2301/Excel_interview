from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings

SYSTEM_PROMPT = (
    "You are an expert Microsoft Excel interviewer. Score the candidate succinctly. "
    "Return JSON matching the schema with: score (0-100), strengths (array of bullet strings), improvements (array), and summary."
)

JSON_SCHEMA = {
    "name": "excel_interview_grade",
    "schema": {
        "type": "object",
        "properties": {
            "score": {"type": "number", "minimum": 0, "maximum": 100},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "improvements": {"type": "array", "items": {"type": "string"}},
            "summary": {"type": "string"},
        },
        "required": ["score"],
        "additionalProperties": False,
    },
}


class RubricGrader:
    """Invokes an LLM rubric scorer with structured criteria."""

    async def grade(self, payload: dict[str, Any]) -> dict[str, Any]:
        question = payload.get("question", {})
        answer_payload = payload.get("answer_payload", {})
        question_prompt = payload.get("question_prompt") or question.get("prompt") or ""
        answer_text = answer_payload.get("text") or payload.get("answer") or ""

        if not answer_text.strip() or not settings.openai_api_key:
            return self._fallback()

        body = {
            "model": settings.default_model or "gpt-4o-mini",
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": SYSTEM_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Question:\n" + question_prompt + "\n\n" +
                                "Candidate answer:\n" + answer_text
                            ),
                        }
                    ],
                },
            ],
            "response_format": {"type": "json_schema", "json_schema": JSON_SCHEMA},
        }

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers=headers,
                    json=body,
                )
            response.raise_for_status()
            data = response.json()
            parsed = self._extract_json(data)
            if not parsed:
                return self._fallback()
            score = float(parsed.get("score", 0.0))
            strengths = parsed.get("strengths", []) or []
            improvements = parsed.get("improvements", []) or []
            summary = parsed.get("summary", "")
            auto_feedback = self._format_feedback(strengths, improvements)
            return {
                "score": score,
                "objective": {
                    "strengths": strengths,
                    "improvements": improvements,
                },
                "notes": summary,
                "auto_feedback": auto_feedback,
            }
        except Exception:
            return self._fallback(answer_text)

    def _extract_json(self, data: dict[str, Any]) -> dict[str, Any] | None:
        for item in data.get("output", []):
            for chunk in item.get("content", []):
                if chunk.get("type") == "output_json_schema":
                    return chunk.get("json")
        return None

    def _format_feedback(self, strengths: list[str], improvements: list[str]) -> str:
        parts = []
        if strengths:
            parts.append("Strengths: " + "; ".join(strengths))
        if improvements:
            parts.append("Focus areas: " + "; ".join(improvements))
        return "\n".join(parts) if parts else "Great work—thanks for the answer."

    def _fallback(self, answer: str | None = None) -> dict[str, Any]:
        base_score = 55.0
        if answer:
            text = answer.lower()
            if "excel" in text:
                base_score += 15
            if any(keyword in text for keyword in ["pivot", "vlookup", "xlookup", "index", "match"]):
                base_score += 10
            base_score = min(base_score, 90.0)
        return {
            "score": base_score,
            "objective": {"strengths": [], "improvements": []},
            "notes": "Heuristic fallback score",
            "auto_feedback": "Thanks for the answer—consider adding more concrete Excel specifics next time.",
        }


rubric_grader = RubricGrader()
