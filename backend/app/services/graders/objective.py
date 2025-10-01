from __future__ import annotations

from typing import Any


class ObjectiveGrader:
    """Validates MCQ and short-answer responses against objective criteria."""

    async def grade(self, payload: dict[str, Any]) -> dict[str, Any]:
        # TODO: Implement objective grading logic
        _ = payload
        return {"score": 0.0, "objective": {}, "notes": "Objective grading not yet implemented"}


objective_grader = ObjectiveGrader()
