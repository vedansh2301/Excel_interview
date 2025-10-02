from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.tools import (
    FinalizeSessionResponse,
    GetNextQuestionResponse,
    GradeAnswerPayload,
    GradeAnswerResponse,
    LogInteractionPayload,
    LogInteractionResponse,
    RecordOutcomePayload,
    RecordOutcomeResponse,
    SessionPayload,
    UpdateDifficultyResponse,
)
from app.services import memory_service, storage_service
from app.services.difficulty import difficulty_service
from app.services.orchestrator import orchestrator_service
from app.services.graders import formula_grader, objective_grader, rubric_grader

router = APIRouter(prefix="/tools", tags=["tools"])


@router.options("/get_next_question")
async def options_get_next_question() -> JSONResponse:
    return JSONResponse(status_code=200, content={})


@router.post("/get_next_question", response_model=GetNextQuestionResponse)
async def get_next_question(payload: SessionPayload) -> dict:
    context = await orchestrator_service.fetch_context(payload.session_id)
    plan = context.get("question_plan", [])
    plan_index = int(context.get("plan_index", 0))
    asked_questions = set(context.get("asked_questions", []))

    target_skill = "general"
    target_difficulty = 2
    completed = False

    if plan and plan_index < len(plan):
        entry = plan[plan_index]
        target_skill = str(entry.get("skill", "general"))
        target_difficulty = int(entry.get("difficulty", 2))
    elif plan and plan_index >= len(plan):
        completed = True

    candidates = await storage_service.list_questions_by_skill(target_skill, target_difficulty)
    question = next((q for q in candidates if q.get("_id") not in asked_questions), None)

    if question is None and not completed:
        fallback = await storage_service.get_any_question()
        if fallback and fallback.get("_id") not in asked_questions:
            question = fallback

    question_payload = None
    if question is not None:
        question_payload = {
            "id": str(question.get("_id")),
            "skill": question.get("skill", "general"),
            "difficulty": int(question.get("difficulty", 2)),
            "type": question.get("type", "open"),
            "prompt": question.get("prompt", ""),
            "weight": float(question.get("weight", 1.0)),
            "meta": question.get("meta", {}),
        }
        asked_list = context.get("asked_questions", [])
        asked_list.append(question_payload["id"])
        context["asked_questions"] = asked_list

        if plan and plan_index < len(plan):
            context["plan_index"] = plan_index + 1
        else:
            context["plan_index"] = plan_index
    else:
        completed = True
        context["plan_index"] = max(plan_index, len(plan))

    context["current_question"] = question_payload
    await orchestrator_service.store_memory(payload.session_id, context)

    remaining = None
    if plan:
        remaining = max(len(plan) - context.get("plan_index", 0), 0)
        if context.get("plan_index", 0) >= len(plan):
            completed = True

    return {
        "question": question_payload,
        "rating_summary": context.get("rating_summary", {}),
        "plan_index": context.get("plan_index", 0),
        "remaining": remaining,
        "completed": completed,
    }


@router.options("/grade_answer")
async def options_grade_answer() -> JSONResponse:
    return JSONResponse(status_code=200, content={})


@router.post("/grade_answer", response_model=GradeAnswerResponse)
async def grade_answer(payload: GradeAnswerPayload) -> GradeAnswerResponse:
    # TODO: Route to appropriate grader based on question type
    question = await storage_service.get_question(payload.question_id)
    question_type = question.get("type") if question is not None else "open"

    if question_type in {"mcq", "short_text", "shortcut"}:
        result = await objective_grader.grade(payload.model_dump())
    elif question_type in {"formula", "excel_formula"}:
        result = await formula_grader.grade({
            "question": question.get("meta") if question else {},
            "answer_payload": payload.answer_payload,
        })
    else:
        result = await rubric_grader.grade(
            {
                "question": question or {},
                "question_prompt": (question or {}).get("prompt", payload.answer_payload.get("question_prompt")),
                "answer_payload": payload.answer_payload,
            }
        )
    return GradeAnswerResponse(**result)


@router.options("/record_outcome")
async def options_record_outcome() -> JSONResponse:
    return JSONResponse(status_code=200, content={})


@router.post("/record_outcome", response_model=RecordOutcomeResponse)
async def record_outcome(payload: RecordOutcomePayload) -> RecordOutcomeResponse:
    # TODO: Persist attempt data and analytics
    session_id = payload.session_id
    question_id = payload.question_id
    if not session_id:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    meta = payload.meta or {}

    await storage_service.record_attempt(
        session_id=session_id,
        question_id=question_id,
        score=payload.score,
        objective=meta.get("objective"),
        time_ms=payload.time_ms,
        difficulty=payload.difficulty,
        answer_payload=meta.get("answer_payload", {}),
        feedback=meta.get("feedback"),
        hints_used=meta.get("hints_used", 0),
    )

    skill = meta.get("skill")
    if isinstance(skill, str):
        await storage_service.update_skill_metrics(
            session_id=session_id,
            skill=skill,
            score=payload.score,
            difficulty=payload.difficulty,
            hints_used=meta.get("hints_used", 0),
        )

    updated_states = await storage_service.list_skill_states(session_id)
    rating_summary: dict[str, float] = {}
    if updated_states:
        skill_states_payload = [
            {
                "skill": state.get("skill"),
                "rating": state.get("rating", 50),
                "target_difficulty": state.get("target_difficulty", 2),
                "asked_count": state.get("asked_count", 0),
                "correct_count": state.get("correct_count", 0),
            }
            for state in updated_states
        ]
        rating_summary = {
            entry["skill"]: entry["rating"]
            for entry in skill_states_payload
            if entry.get("skill")
        }
        cached_context = await orchestrator_service.fetch_context(session_id)
        cached_context["skill_states"] = skill_states_payload
        cached_context["rating_summary"] = rating_summary
        await orchestrator_service.store_memory(session_id, cached_context)

    return RecordOutcomeResponse(ok=True, rating_summary=rating_summary)


@router.options("/update_difficulty")
async def options_update_difficulty() -> JSONResponse:
    return JSONResponse(status_code=200, content={})


@router.post("/update_difficulty", response_model=UpdateDifficultyResponse)
async def update_difficulty(payload: SessionPayload) -> UpdateDifficultyResponse:
    result = await difficulty_service.update_difficulty(payload.session_id)
    return UpdateDifficultyResponse(new_level=result.new_level, rationale=result.rationale)


@router.options("/finalize_session")
async def options_finalize_session() -> JSONResponse:
    return JSONResponse(status_code=200, content={})


@router.post("/finalize_session", response_model=FinalizeSessionResponse)
async def finalize_session(payload: SessionPayload) -> FinalizeSessionResponse:
    session_id = payload.session_id
    if not session_id:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    attempts = await storage_service.list_attempts(session_id)
    total_attempts = len(attempts)
    average_score = sum(float(item.get("score", 0.0)) for item in attempts) / total_attempts if attempts else 0.0
    context = await orchestrator_service.fetch_context(session_id)
    rating_summary = context.get("rating_summary", {})
    strengths = [skill.replace("_", " ") for skill, rating in rating_summary.items() if rating >= 70]
    growth = [skill.replace("_", " ") for skill, rating in rating_summary.items() if rating < 60]

    strength_text = strengths if strengths else ["Excel fundamentals"]
    growth_text = growth if growth else ["refining explanations to add more detail"]

    if rating_summary:
        overall = sum(rating_summary.values()) / len(rating_summary)
    else:
        overall = average_score * 100 if average_score <= 1 else average_score

    summary = (
        f"We covered {total_attempts} questions; your overall score sits at {overall:.0f}/100.\n"
        f"Strengths: {', '.join(strength_text)}.\n"
        f"Focus areas: {', '.join(growth_text)}."
    )
    return FinalizeSessionResponse(report_url=f"https://reports.example.com/{payload.session_id}", summary=summary)


@router.options("/log_interaction")
async def options_log_interaction() -> JSONResponse:
    return JSONResponse(status_code=200, content={})


@router.post("/log_interaction", response_model=LogInteractionResponse)
async def log_interaction(payload: LogInteractionPayload) -> LogInteractionResponse:
    session_id = payload.session_id
    if not session_id:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    event_data = payload.payload or {}
    plan = str(event_data.get("plan", payload.event_type))
    action = str(event_data.get("action", event_data.get("utterance", payload.event_type)))
    outcome = str(event_data.get("outcome", event_data.get("result", "logged")))
    metrics = event_data.get("metrics") if isinstance(event_data.get("metrics"), dict) else None
    flagged = bool(event_data.get("flagged", False))

    step_id = str(event_data.get("step_id", payload.event_type))

    await storage_service.log_agent_event(
        session_id=session_id,
        step_id=step_id,
        plan=plan,
        action=action,
        outcome=outcome,
        metrics=metrics,
        flagged=flagged,
    )

    if payload.event_type in {"question_asked", "answer_received", "feedback_shared"}:
        await memory_service.append_transcript_turn(
            payload.session_id,
            {
                "event_type": payload.event_type,
                "payload": event_data,
                "created_at": payload.created_at.isoformat(),
            },
        )
    return LogInteractionResponse(ok=True)
