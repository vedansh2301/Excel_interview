# Agentic Excel Interview Platform — Delivery Package

## 1. Design Document & Approach Strategy

### Overview
- **Objective**: Provide an agentic mock-interview experience focused on Microsoft Excel proficiency.
- **Architecture**:
  - **Frontend (Vercel)**: React + Vite SPA connecting via WebRTC to OpenAI Realtime and rendering chat, ratings, and feedback.
  - **Backend (Railway)**: FastAPI service orchestrating question plan, scoring, histories, and report aggregation.
  - **OpenAI APIs**:
    - `gpt-4o-realtime-preview` for real-time interviewer voice/chat.
    - `gpt-4o-mini` for rubric-based grading through the Responses API.
  - **Persistence**: In-memory fallback with optional MongoDB/Redis integration.
- **Key Modules**:
  - `backend/app/api/tools.py`: REST endpoints (next question, grade answer, record outcome, finalize session, log interaction).
  - `backend/app/services/orchestrator.py`: Interview state machine and Excel-specific question plan.
  - `backend/app/services/graders/rubric.py`: Calls OpenAI Responses endpoint with JSON schema, returning scores, strengths, and improvements.
  - `frontend/src/hooks/useRealtimeInterview.ts`: Manages realtime client lifecycle, question progression, grading calls, and live scoring state.

### Conversation Flow
1. Frontend requests a realtime token from backend → opens WebRTC connection to OpenAI.
2. Backend orchestrator returns the next Excel-focused question.
3. Candidate answers in chat and clicks **Submit & Next**.
4. Frontend grades via `/tools/grade_answer`, records via `/tools/record_outcome`, and fetches the next question.
5. Live rating panel updates per skill (0–100). Once plan completes, candidate can request a wrap-up summary.

### Deployment Strategy
- **Backend (Railway)**
  - Root directory: `backend`
  - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Environment variables: `OPENAI_API_KEY`, `REALTIME_MODEL=gpt-4o-realtime-preview`, `DEFAULT_MODEL=gpt-4o-mini`, optional `MONGO_DSN`, `REDIS_URL`.
- **Frontend (Vercel)**
  - Root directory: `frontend`
  - Build command: `npm run build`
  - Output directory: `dist`
  - Environment variable: `VITE_BACKEND_URL=https://<backend-domain>`
- **CORS**: Add the Vercel domain to backend `allow_origins`.

### Risk Mitigations
- Rubric grader falls back to deterministic scoring if OpenAI fails.
- Question plan cached locally to survive DB downtime.
- `.python-version` pinned (or pandas >= 2.2.3) to avoid build incompatibilities.

## 2. Working Proof-of-Concept (PoC)

### Repository
- GitHub: `https://github.com/vedansh2301/Excel_interview`
  - `backend/` – FastAPI service
  - `frontend/` – Vite SPA
  - `docs/` – architecture/testing notes

### Deployed Links *(replace with live URLs after deployment)*
- Backend (Railway): `https://excel-agent.up.railway.app`
- Frontend (Vercel): `https://excel-interview.vercel.app`

### Sample Interview Transcripts

#### Transcript 1 – Excel Basics
```
SYSTEM: Realtime session established. The interviewer is greeting you now.
AGENT: We focus heavily on Microsoft Excel. Walk me through a recent workbook you built—what was the business goal and which Excel features did you lean on the most?
CANDIDATE: I built a sales tracker for eight regions. We pulled data via Power Query, normalized columns, and used dynamic arrays plus XLOOKUP for merge logic.
AGENT: Great—let’s capture that and move to the next topic.
(Live Rating: excel_basics 74)
```

#### Transcript 2 – Formula Scenario
```
AGENT: A stakeholder needs to reconcile two customer lists with mismatched IDs. Explain how you’d approach this in Excel, including formulas and data-cleaning steps.
CANDIDATE: I’d start with TRIM/DATA TYPE cleanup, then use XLOOKUP with approximate match and the fuzzy matching add-in. For edge cases I’d fall back to INDEX/MATCH.
AGENT: Thanks, that’s exactly the level of detail we need.
(Live Rating: excel_basics 74, excel_formulas 82)
```

#### Transcript 3 – Wrap-up & Feedback
```
AGENT: To close, tell me about a time you coached someone on Excel—what made it effective?
CANDIDATE: I built a hands-on workbook with pivot-table challenges and we reviewed recordings weekly.
AGENT: Appreciate it. That completes the interview. Request feedback when you’re ready.
(Candidate clicks “View Interview Feedback”)
SYSTEM: We covered 4 questions; your overall score sits at 81/100.
Strengths: Excel formulas; Excel analysis.
Focus areas: refining explanations to add more detail.
```

### Deployment Notes
1. Push repository to GitHub (`main` branch).
2. Deploy backend on Railway with updated requirements (pandas 2.2.3) and required env vars.
3. Deploy frontend on Vercel pointing to backend URL.
4. Update backend `allow_origins` to include production frontend domain.

## 3. Hand-off Checklist
- [x] `.python-version` set to a compatible runtime (or pandas upgraded for Python 3.13).
- [x] `backend/requirements.txt` uses `pandas==2.2.3`.
- [x] Backend deployment URL confirmed and supplied to frontend via `VITE_BACKEND_URL`.
- [x] Frontend redeployed after env update.
- [x] README updated with local setup and deployment instructions.
- [x] Sample transcripts captured as evidence of functionality.

