# QueueStorm Warmup — bKash SUST CSE Carnival 2026

A small full-stack service for the **Mock Preliminary Round** of the
bKash SUST CSE Carnival 2026 Codex Community Hackathon.

It reads a customer support message and returns a structured
classification (case type, severity, department, agent summary,
human-review flag, confidence) over HTTPS.

## Stack

| Layer    | Tech                                             |
| -------- | ------------------------------------------------ |
| Backend  | Python 3.11+ · FastAPI · Pydantic · pytest      |
| Frontend | Vite · React 18 · TypeScript · Tailwind CSS      |
| Hosting  | Single service (Render / Railway / Fly) — FastAPI serves both API and built frontend |

The classification is **rules-based** (no LLM required, no API key, no
GPU dependency).

## Repository Layout

```
App/
├── backend/                 FastAPI service
│   ├── app/
│   │   ├── main.py          /health, /sort-ticket, mounts frontend/dist
│   │   ├── classifier.py    Rules-based classification engine
│   │   ├── safety.py        agent_summary safety scrubber
│   │   └── schemas.py       Pydantic models
│   ├── tests/
│   │   └── test_classifier.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/                Vite + React + TS + Tailwind UI
│   ├── src/
│   ├── package.json
│   └── README.md
├── docker-compose.yml       Optional: spin up backend in a container
└── README.md                ← you are here
```

## Endpoints

### `GET /health`

Returns service liveness.

```json
{ "status": "ok", "service": "queuestorm-warmup" }
```

### `POST /sort-ticket`

Request:

```json
{
  "ticket_id": "T-001",
  "channel": "app",
  "locale": "en",
  "message": "I sent 3000 taka to wrong number this morning, please help"
}
```

Response:

```json
{
  "ticket_id": "T-001",
  "case_type": "wrong_transfer",
  "severity": "high",
  "department": "dispute_resolution",
  "agent_summary": "Customer reports sending 3000 taka to the wrong recipient and asks for help recovering the funds.",
  "human_review_required": false,
  "confidence": 0.85
}
```

## Run Locally

### Backend

```bash
cd App/backend
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- http://localhost:8000/health
- http://localhost:8000/docs (Swagger UI)

### Frontend (dev mode)

In another terminal:

```bash
cd App/frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api/*` to the backend on
`:8000`.

### Frontend (production build, served by FastAPI)

```bash
cd App/frontend
npm install
npm run build                # writes to App/frontend/dist
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Now visit http://localhost:8000 — the React app loads from FastAPI
and `/health` and `/sort-ticket` are available on the same origin.

## Run Tests

```bash
cd App/backend
pytest -v
```

Tests cover the five sample cases from `Problem.txt`, the safety rule
(never instruct the customer to share PIN/OTP/password), Bengali
messages, and edge cases.

## Sample Cases

| # | Message (excerpt)                                        | Expected case_type                          | Severity |
| - | -------------------------------------------------------- | ------------------------------------------- | -------- |
| 1 | "I sent 3000 to wrong number"                            | `wrong_transfer`                            | high     |
| 2 | "Payment failed but balance deducted"                    | `payment_failed`                            | high     |
| 3 | "Someone called asking my OTP, is that bKash?"           | `phishing_or_social_engineering`            | critical |
| 4 | "Please refund my last transaction, I changed my mind"   | `refund_request`                            | low      |
| 5 | "App crashed when I opened it"                           | `other`                                     | low      |

## Safety

The grader will auto-fail any response whose `agent_summary` asks the
customer to share PIN, OTP, password, or full card number.

We defend against this in two layers:

1. The summary builder (`classifier._build_summary`) never produces
   such instructions — it only describes the situation.
2. `safety.scrub` runs as the **last** step before returning the
   response and strips any imperative "share/send/give/verify your X"
   phrasing, replacing it with a neutral safety line.

## Deployment

A single service that hosts both API and UI is the simplest path:

**Render / Railway / Fly** — set:

- **Build command:**
  ```bash
  cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt
  ```
- **Start command:**
  ```bash
  cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
- **Environment variables:** none required (optional: `CORS_ORIGINS`).

HTTPS is handled by the platform automatically. The resulting URL like
`https://queuestorm-warmup.onrender.com` exposes:

- `GET  /health`
- `POST /sort-ticket`
- `GET  /` (the React dashboard)

## LLM Usage

**No LLM is used.** Classification is rules-based, deterministic, and
runs in microseconds.

## Known Limits

- Classification is English/Bengali keyword-based. Mixed languages or
  heavy transliteration may produce noisy results. The mock round
  scope does not require multilingual robustness.
- No persistent storage — each request is stateless.

## License

This is a hackathon submission; no specific license is claimed.
