# Agentic Excel Interview Platform

An agentic interview simulator that pairs a FastAPI backend, OpenAI Realtime voice/chat session, and a React/Vite frontend. The interviewer agent conducts a structured Excel-focused interview, grades every answer in real time, and streams live ratings and feedback to the candidate.

## Features
- **OpenAI Realtime Agent**: WebRTC connection that voices concise questions, waits for responses, and acknowledges before advancing.
- **Excel-first Interview Plan**: Built-in question plan covering Excel basics, formulas, analysis, and professionalism with fallback prompts when MongoDB is offline.
- **Live Scoring**: Each answer is fed through the OpenAI Responses API (JSON schema) to produce a 0–100 score plus strengths/growth areas.
- **Adaptive Ratings**: Scores are persisted per skill and surface immediately in the UI.
- **Feedback & Wrap-up**: One-click feedback summarizes strengths, focus areas, and overall score.

## Repo Layout
```
backend/  # FastAPI project (tool endpoints, grading, realtime token proxy)
frontend/ # Vite + React app (WebRTC client, chat UI, ratings panel)
docs/     # Architecture & testing notes
```

## Prerequisites
- Python 3.11
- Node.js 18+
- An OpenAI API key with access to `gpt-4o-realtime-preview` and `gpt-4o-mini`
- (Optional) MongoDB & Redis. The app gracefully falls back to in-memory storage if they’re not running.

## Local Setup

### Backend
```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# copy env template and edit
cp ../.env ../.env.local  # or create manually
# ensure .env has: OPENAI_API_KEY, REALTIME_MODEL=gpt-4o-realtime-preview

/opt/homebrew/opt/python@3.11/bin/python3.11 -m uvicorn app.main:app --reload
```
The backend exposes:
- `POST /api/v1/realtime/session-token`
- `POST /api/v1/tools/get_next_question`
- `POST /api/v1/tools/grade_answer`
- `POST /api/v1/tools/record_outcome`
- `POST /api/v1/tools/finalize_session`

### Frontend
```bash
cd frontend
npm install
cp .env.example .env  # adjust VITE_BACKEND_URL if backend isn’t localhost:8000
npm run dev -- --host=127.0.0.1 --port=5173
```
Visit http://127.0.0.1:5173, allow microphone access, click **Start Session**, and answer the prompts. After each answer click **Submit & Next** to advance and update the live rating.

## Environment Variables
| Key                | Description                                      |
|--------------------|--------------------------------------------------|
| `OPENAI_API_KEY`   | Required. Must have Realtime + Responses access. |
| `REALTIME_MODEL`   | Defaults to `gpt-4o-realtime-preview`.           |
| `DEFAULT_MODEL`    | Defaults to `gpt-4o-mini` for grading.           |
| `MONGO_DSN`        | Optional. Leave blank to use in-memory store.    |
| `REDIS_URL`        | Optional. Leave blank if Redis not available.    |
| `VITE_BACKEND_URL` | Frontend base URL for API calls.                 |

## Deployment

### 1. Backend (FastAPI)
Vercel’s Python runtime is designed for lightweight serverless functions; the realtime WebRTC token exchange and OpenAI calls work best on a long-lived server. Suggested options:
- **Railway** (https://railway.app)** or **Render** (https://render.com)**: Both run FastAPI with minimal config.
- **Fly.io** or **Docker-capable VPS** if you prefer container deployment.

Example with Railway:
1. Push this repo to GitHub/GitLab.
2. Create a Railway account and select **Deploy from GitHub**.
3. Choose the repo, set **Root Directory** to `backend`, and define a new environment -> `python` with start command:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
   ```
4. Add the following variables in Railway:
   - `OPENAI_API_KEY`
   - `REALTIME_MODEL=gpt-4o-realtime-preview`
   - `DEFAULT_MODEL=gpt-4o-mini`
   - (Optional) `MONGO_DSN`, `REDIS_URL`
5. Deploy. Railway will give you a public HTTPS URL (e.g., `https://excel-agent.up.railway.app`).

### 2. Frontend (Vercel)
1. Install the Vercel CLI (`npm i -g vercel`) or use the web UI.
2. Create a new Vercel project pointing at the `frontend` directory.
3. Configure environment variables:
   - `VITE_BACKEND_URL=https://<your-backend-domain>`
4. Update the build settings (Vercel auto-detects Vite):
   - Build command: `npm run build`
   - Output dir: `dist`
5. Deploy. Vercel serves the static site globally. Make sure the backend domain is reachable and CORS allows Vercel’s origin (add it to `backend/app/main.py` `allow_origins`).

### Optional: Add CORS Origin
For a hosted frontend (e.g., `https://your-app.vercel.app`), add that URL to `allow_origins` inside `backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://your-app.vercel.app",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Redeploy the backend after updating the list.

## Usage Tips
- Click **Submit & Next** after each answer to trigger AI grading and move to the next question.
- The live rating panel reflects the latest per-skill score (0–100). Once all questions are answered, use **View Interview Feedback** for a strengths/focus summary.
- If OpenAI rate limits or returns errors, the system falls back to a heuristic score and logs the issue in the console.

## Future Enhancements
- Persist sessions and transcripts in MongoDB/Redis once those services are configured.
- Add authentication and candidate management.
- Replace heuristic fallback with cached grading prompts for offline testing.

## License
MIT (or update to your preferred license).

