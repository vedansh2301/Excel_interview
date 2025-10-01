from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

SAMPLE_QUESTIONS: list[dict[str, Any]] = [
    {
        "_id": "q_intro_1",
        "skill": "excel_basics",
        "difficulty": 2,
        "type": "open",
        "prompt": "We focus heavily on Microsoft Excel. Walk me through a recent workbook you built—what was the business goal and which Excel features did you lean on the most?",
        "weight": 1.0,
        "meta": {},
    },
    {
        "_id": "q_tech_1",
        "skill": "excel_formulas",
        "difficulty": 2,
        "type": "open",
        "prompt": "A stakeholder needs to reconcile two customer lists with mismatched IDs. Explain how you would approach this in Excel, including the exact formulas or functions you would combine and any data-cleaning steps.",
        "weight": 1.0,
        "meta": {},
    },
    {
        "_id": "q_design_1",
        "skill": "excel_analysis",
        "difficulty": 3,
        "type": "open",
        "prompt": "You receive a dump of 50k sales rows. Describe how you would build an analysis in Excel that surfaces the top 3 performance drivers, including pivot tables, charts, or Power Query steps you would rely on.",
        "weight": 1.0,
        "meta": {},
    },
    {
        "_id": "q_wrap_1",
        "skill": "professionalism",
        "difficulty": 1,
        "type": "behavioral",
        "prompt": "To close, tell me about a time you coached someone on Excel—what made it effective and what would you do differently next time?",
        "weight": 1.0,
        "meta": {},
    },
]


class StorageService:
    """Data access abstractions backed by MongoDB collections."""

    def __init__(self) -> None:
        self._db: AsyncIOMotorDatabase | None = None
        self._memory_sessions: dict[str, dict[str, Any]] = {}
        self._memory_skill_state: dict[str, dict[str, Any]] = defaultdict(dict)
        self._memory_attempts: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._memory_agent_events: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def configure(self, db: AsyncIOMotorDatabase | None) -> None:
        self._db = db

    def _require_db(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise RuntimeError("Mongo database not configured. Call connect_to_mongo during startup.")
        return self._db

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        if self._db is None:
            return self._memory_sessions.get(session_id)
        db = self._require_db()
        return await db.sessions.find_one({"_id": session_id})

    async def get_question(self, question_id: str | None) -> dict[str, Any] | None:
        if question_id is None:
            return None
        if self._db is None:
            return next((q for q in SAMPLE_QUESTIONS if q["_id"] == question_id), None)
        db = self._require_db()
        return await db.questions.find_one({"_id": question_id})

    async def list_questions_by_skill(self, skill: str, difficulty: int, limit: int = 50) -> list[dict[str, Any]]:
        if self._db is None:
            matched = [q for q in SAMPLE_QUESTIONS if q["skill"] == skill and q["difficulty"] == difficulty]
            return matched[:limit]
        db = self._require_db()
        cursor = (
            db.questions.find({"skill": skill, "difficulty": difficulty})
            .sort("_id", 1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def get_any_question(self) -> dict[str, Any] | None:
        if self._db is None:
            return SAMPLE_QUESTIONS[0] if SAMPLE_QUESTIONS else None
        db = self._require_db()
        cursor = db.questions.find().sort([("difficulty", 1), ("_id", 1)]).limit(1)
        results = await cursor.to_list(length=1)
        return results[0] if results else None

    async def upsert_session_skill_state(
        self,
        *,
        session_id: str,
        skill: str,
        defaults: dict[str, Any],
    ) -> dict[str, Any]:
        now = datetime.utcnow()
        if self._db is None:
            session_state = self._memory_skill_state[session_id]
            entry = session_state.get(skill)
            if entry is None:
                entry = {
                    "session_id": session_id,
                    "skill": skill,
                    "created_at": now,
                }
            entry.update(
                {
                    "rating": defaults.get("rating", 50),
                    "target_difficulty": defaults.get("target_difficulty", 2),
                    "asked_count": defaults.get("asked_count", 0),
                    "correct_count": defaults.get("correct_count", 0),
                    "updated_at": now,
                }
            )
            session_state[skill] = entry
            return entry

        db = self._require_db()
        collection = db.session_skill_state
        existing = await collection.find_one({"session_id": session_id, "skill": skill})
        payload = {
            "session_id": session_id,
            "skill": skill,
            "rating": defaults.get("rating", 50),
            "target_difficulty": defaults.get("target_difficulty", 2),
            "asked_count": defaults.get("asked_count", 0),
            "correct_count": defaults.get("correct_count", 0),
            "updated_at": now,
        }
        if existing is None:
            payload["created_at"] = now
            await collection.insert_one(payload)
            return payload

        await collection.update_one(
            {"_id": existing["_id"]},
            {"$set": payload},
        )
        existing.update(payload)
        return existing

    async def list_skill_states(self, session_id: str) -> list[dict[str, Any]]:
        if self._db is None:
            return list(self._memory_skill_state.get(session_id, {}).values())
        db = self._require_db()
        cursor = db.session_skill_state.find({"session_id": session_id}).sort("skill", 1)
        return await cursor.to_list(length=None)

    async def record_attempt(
        self,
        *,
        session_id: str,
        question_id: str | None,
        score: float,
        objective: dict[str, Any] | None,
        time_ms: int,
        difficulty: int,
        answer_payload: dict[str, Any],
        feedback: str | None,
        hints_used: int,
    ) -> dict[str, Any]:
        now = datetime.utcnow()
        doc = {
            "session_id": session_id,
            "question_id": question_id,
            "score": score,
            "objective": objective,
            "time_ms": time_ms,
            "difficulty": difficulty,
            "answer_payload": answer_payload,
            "feedback": feedback,
            "hints_used": hints_used,
            "created_at": now,
        }
        if self._db is None:
            self._memory_attempts[session_id].append(doc)
            doc["_id"] = f"mem_attempt_{len(self._memory_attempts[session_id])}"
            return doc

        db = self._require_db()
        result = await db.attempts.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def list_recent_attempts(self, session_id: str, limit: int = 5) -> list[dict[str, Any]]:
        if self._db is None:
            return list(reversed(self._memory_attempts.get(session_id, [])))[:limit]
        db = self._require_db()
        cursor = (
            db.attempts.find({"session_id": session_id})
            .sort("created_at", -1)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def log_agent_event(
        self,
        *,
        session_id: str,
        step_id: str,
        plan: str,
        action: str,
        outcome: str,
        metrics: dict[str, Any] | None,
        flagged: bool,
    ) -> dict[str, Any]:
        now = datetime.utcnow()
        doc = {
            "session_id": session_id,
            "step_id": step_id,
            "plan": plan,
            "action": action,
            "outcome": outcome,
            "metrics": metrics,
            "flagged": flagged,
            "created_at": now,
        }
        if self._db is None:
            self._memory_agent_events[session_id].append(doc)
            doc["_id"] = f"mem_event_{len(self._memory_agent_events[session_id])}"
            return doc

        db = self._require_db()
        result = await db.agent_events.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def update_skill_metrics(
        self,
        *,
        session_id: str,
        skill: str,
        score: float,
        difficulty: int,
        hints_used: int,
    ) -> dict[str, Any]:
        now = datetime.utcnow()
        if self._db is None:
            session_state = self._memory_skill_state[session_id]
            entry = session_state.get(skill)
            if entry is None:
                entry = {
                    "session_id": session_id,
                    "skill": skill,
                    "rating": 50,
                    "target_difficulty": difficulty,
                    "asked_count": 0,
                    "correct_count": 0,
                    "created_at": now,
                }
            entry["asked_count"] = int(entry.get("asked_count", 0)) + 1
            entry["rating"] = max(0, min(100, int(entry.get("rating", 50)) + self._rating_delta(score, hints_used=hints_used)))
            entry["target_difficulty"] = difficulty
            if score >= 0.8:
                entry["correct_count"] = int(entry.get("correct_count", 0)) + 1
            entry["updated_at"] = now
            session_state[skill] = entry
            return entry

        db = self._require_db()
        collection = db.session_skill_state
        entry = await collection.find_one({"session_id": session_id, "skill": skill})
        if entry is None:
            entry = {
                "session_id": session_id,
                "skill": skill,
                "rating": 50,
                "target_difficulty": difficulty,
                "asked_count": 0,
                "correct_count": 0,
                "created_at": now,
            }
        entry["asked_count"] = int(entry.get("asked_count", 0)) + 1
        entry["rating"] = max(0, min(100, int(entry.get("rating", 50)) + self._rating_delta(score, hints_used=hints_used)))
        entry["target_difficulty"] = difficulty
        if score >= 0.8:
            entry["correct_count"] = int(entry.get("correct_count", 0)) + 1
        entry["updated_at"] = now
        await collection.update_one(
            {"session_id": session_id, "skill": skill},
            {"$set": entry},
            upsert=True,
        )
        return entry

    async def list_attempts(self, session_id: str) -> list[dict[str, Any]]:
        if self._db is None:
            return list(reversed(self._memory_attempts.get(session_id, [])))
        db = self._require_db()
        cursor = db.attempts.find({"session_id": session_id}).sort("created_at", -1)
        return await cursor.to_list(length=None)

    def _rating_delta(self, score: float, *, hints_used: int) -> int:
        if score >= 0.8:
            delta = 8
        elif score >= 0.6:
            delta = 4
        else:
            delta = -6
        if hints_used > 0 and delta > 0:
            delta -= 2
        return delta


storage_service = StorageService()
