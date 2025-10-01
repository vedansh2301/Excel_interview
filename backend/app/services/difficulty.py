from __future__ import annotations

from dataclasses import dataclass

from app.services.storage import storage_service


@dataclass
class DifficultyResult:
    new_level: int
    rationale: str


class DifficultyService:
    """Computes adaptive difficulty based on recent performance."""

    async def update_difficulty(self, session_id: str) -> DifficultyResult:
        attempts = await storage_service.list_recent_attempts(session_id, limit=3)
        if not attempts:
            return DifficultyResult(new_level=2, rationale="No attempts yet; maintaining baseline difficulty")

        average_score = sum(float(attempt.get("score", 0.0)) for attempt in attempts) / len(attempts)
        previous_level = int(attempts[0].get("difficulty", 2))

        if average_score >= 0.8 and previous_level < 3:
            new_level = previous_level + 1
            rationale = f"Average score {average_score:.2f} >= 0.80; escalating difficulty to {new_level}"
        elif average_score <= 0.4 and previous_level > 1:
            new_level = previous_level - 1
            rationale = f"Average score {average_score:.2f} <= 0.40; reducing difficulty to {new_level}"
        else:
            new_level = previous_level
            rationale = f"Average score {average_score:.2f}; keeping difficulty at {new_level}"

        return DifficultyResult(new_level=new_level, rationale=rationale)


difficulty_service = DifficultyService()
