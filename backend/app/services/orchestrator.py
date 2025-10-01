from __future__ import annotations

from typing import Any

from app.services.memory import memory_service
from app.services.storage import storage_service


class OrchestratorService:
    """Provides session context and state transitions for the agent."""

    def __init__(self) -> None:
        self._fallback_context: dict[str, dict[str, Any]] = {}

    async def fetch_context(self, session_id: str) -> dict[str, Any]:
        cached = await memory_service.get_session_context(session_id)
        if cached is not None:
            cached["session_id"] = session_id
            cached.setdefault("question_plan", self._stage_plan())
            cached.setdefault("plan_index", 0)
            cached.setdefault("asked_questions", [])
            return cached

        if session_id in self._fallback_context:
            context = self._fallback_context[session_id]
            context.setdefault("question_plan", self._stage_plan())
            context.setdefault("plan_index", 0)
            context.setdefault("asked_questions", [])
            return context

        session = await storage_service.get_session(session_id)
        if session is None:
            context = self._default_context(session_id)
            self._fallback_context[session_id] = context
            await memory_service.set_session_context(session_id, context)
            return context

        skill_states = await storage_service.list_skill_states(session_id)
        normalized_skill_states = [
            {
                "skill": state.get("skill"),
                "rating": state.get("rating", 50),
                "target_difficulty": state.get("target_difficulty", 2),
                "asked_count": state.get("asked_count", 0),
                "correct_count": state.get("correct_count", 0),
            }
            for state in skill_states
        ]

        recent_transcript = await memory_service.get_recent_transcript(session_id)

        context = {
            "session_id": session_id,
            "stage": self._derive_stage(session.get("status", "in_progress")),
            "skill_rotation": [state["skill"] for state in normalized_skill_states if state.get("skill")],
            "pending_followups": [],
            "skill_states": normalized_skill_states,
            "rating_summary": {
                state["skill"]: state["rating"]
                for state in normalized_skill_states
                if state.get("skill")
            },
            "recent_transcript": recent_transcript,
            "question_plan": self._stage_plan(),
            "plan_index": 0,
            "asked_questions": [],
        }
        await memory_service.set_session_context(session_id, context)
        self._fallback_context[session_id] = context
        return context

    async def store_memory(self, session_id: str, memory: dict[str, Any]) -> None:
        await memory_service.set_session_context(session_id, memory)
        self._fallback_context[session_id] = memory
        skill_entries = memory.get("skill_states", [])
        if isinstance(skill_entries, list):
            for entry in skill_entries:
                skill = entry.get("skill")
                if not isinstance(skill, str):
                    continue
                defaults = {
                    "rating": entry.get("rating", 50),
                    "target_difficulty": entry.get("target_difficulty", 2),
                    "asked_count": entry.get("asked_count", 0),
                    "correct_count": entry.get("correct_count", 0),
                }
                await storage_service.upsert_session_skill_state(
                    session_id=session_id,
                    skill=skill,
                    defaults=defaults,
                )

    def _derive_stage(self, status: str) -> str:
        mapping = {
            "created": "intro",
            "in_progress": "core",
            "completed": "wrap",
        }
        return mapping.get(status, "core")

    def _default_context(self, session_id: str) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "stage": "intro",
            "skill_rotation": [],
            "pending_followups": [],
            "skill_states": [],
            "rating_summary": {},
            "recent_transcript": [],
            "question_plan": self._stage_plan(),
            "plan_index": 0,
            "asked_questions": [],
        }

    def _stage_plan(self) -> list[dict[str, Any]]:
        return [
            {"skill": "excel_basics", "difficulty": 2},
            {"skill": "excel_formulas", "difficulty": 2},
            {"skill": "excel_analysis", "difficulty": 3},
            {"skill": "professionalism", "difficulty": 1},
        ]

orchestrator_service = OrchestratorService()
