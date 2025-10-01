# Agentic Interview Platform Architecture

## Overview
This document captures the initial architectural blueprint for transforming the interview platform into an agentic system powered by OpenAI Realtime and tool calling.

## Key Principles
- **Plan-Act-Reflect Loop**: The interviewer agent forms an internal plan, executes tool calls, observes outcomes, and reflects before the next user-facing response.
- **Tool-First Services**: Backend services are exposed as stateless tools with clear contracts, enabling the agent to call them adaptively.
- **Persistent Memory**: Session memory (transcripts, metrics, reflections) is persisted for reasoning, analytics, and replay.
- **Safety & Guardrails**: Declarative policies, anomaly detection, and controlled fallbacks ensure reliable operation.

## Component Overview

### Realtime Agent Layer
- OpenAI Realtime session with system prompt enforcing interviewer persona, stage hints, safety policies, and tool usage contracts.
- Wrapper orchestrates planning (`plan`), tool invocation (`actions`), observation logging (`log_interaction`), and reflection before emitting interviewer speech.
- Supports multimodal actions (voice, text, hints, file prompts) via structured action payloads consumed by the React client.

### FastAPI Backend
- **Tool Endpoints**: Each endpoint maps to an agent tool schema (e.g., `get_next_question`, `grade_answer`, `record_outcome`, `update_difficulty`, `finalize_session`, `log_interaction`).
- **Agent Services**:
  - `orchestrator_service`: Provides session context, skill rotation, and stage progression metadata on demand.
  - `difficulty_service`: Implements adaptive difficulty logic as pure functions returning both result and rationale.
  - `grading_services`: Objective, formula, and rubric graders returning structured scores and confidence.
  - `report_service`: Aggregates session analytics, strengths, gaps, and exports JSON/PDF.
  - `memory_service`: Manages Redis + MongoDB persistence for agent plans, reflections, and transcript snapshots.

### Data Layer
- MongoDB collections for candidates, sessions, questions, attempts, session_skill_state, and `agent_events`, enabling flexible schema evolution and rapid iteration.
- Redis cache for live session memory (recent turns, metrics, pending actions).
- S3 storage for datasets, uploads, reports, and archived agent logs.

### React Frontend
- Connects to OpenAI Realtime via WebRTC; renders interviewer speech and actions emitted by the agent.
- Components: `ChatPane`, `QuestionCard`, `FormulaInput`, `Timer`, `Progress`, `HintButton`, `FeedbackToast`, `ReportView`, plus agent-driven remediation modals.
- Subscribes to agent action stream for deterministic playback and QA simulation.

### Observability & Safety
- Metrics emitted per agent step (tool latency, retries, confidence deltas) to dashboards.
- Watchdogs enforce conversation length, hint budgets, grading variance; automatic fallback to scripted flow when thresholds breached.
- Policy enforcement layer applies whitelisted Excel functions, data retention rules, and antivirus checks on uploads.

## Milestone Alignment
1. Scaffold backend services and tool schemas.
2. Implement agent wrapper and memory pipeline.
3. Wire React client to agent action stream.
4. Integrate adaptivity, hints, and reporting.
5. QA with personas and finalize documentation.
