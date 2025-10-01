# Realtime & Frontend Smoke Test

This checklist walks through validating the agentic interview stack locally.

## 1. Configure Environment

1. Duplicate `.env.example` → `.env` and populate:
   - `OPENAI_API_KEY` or `REALTIME_API_KEY` with a key that has Realtime access.
   - `MONGO_DSN`, `MONGO_DB_NAME`, `REDIS_URL` as needed.
2. Duplicate `frontend/.env.example` → `frontend/.env` and adjust `VITE_BACKEND_URL` if the backend runs on a non-default host.

## 2. Start Backend

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

### Validate Realtime Session Token

```bash
curl -X POST http://localhost:8000/api/v1/realtime/session-token
```
A successful response includes `client_secret`, `session_id`, and `expires_at`. If the call fails, confirm the API key has Realtime entitlement and outbound networking is allowed.

## 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in the browser, click **Start Session**, and watch the status badge flip to “Realtime Connected.” Use the chat box to send a message and confirm:

- The system logs your message.
- The backend `get_next_question` endpoint fires (check terminal logs).
- Realtime responses stream back as agent messages.

## 4. Troubleshooting

- **Handshake fails**: Inspect browser console and backend logs. Ensure `client_secret` flows from `/realtime/session-token` to the frontend.
- **No audio**: Some models do not emit audio unless `voice` is set. Update `backend/app/api/routes/realtime.py` payload to request a supported voice.
- **CORS**: Vite dev server proxies `/api` to the backend. If you host on another domain, configure `vite.config.ts` proxy accordingly.

Once the loop runs, you can iterate on UI polish, add answer submission flows, and connect grading endpoints for richer feedback.
