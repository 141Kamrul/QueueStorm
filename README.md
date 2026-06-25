# QueueStorm Warmup — bKash SUST CSE Carnival 2026

A small full-stack service for the **Mock Preliminary Round** of the
bKash SUST CSE Carnival 2026 Codex Community Hackathon.

It reads a customer support message and returns a structured
classification (case type, severity, department, agent summary,
human-review flag, confidence) over HTTPS.

## Live Deployment

| Resource          | URL                                              |
| ----------------- | ------------------------------------------------ |
| **Frontend (UI)** | <https://queue-storm-7vjq.vercel.app>            |
| **Backend API**   | <https://queue-storm-7vjq.vercel.app>            |
| `GET  /health`    | <https://queue-storm-7vjq.vercel.app/health>     |
| `POST /sort-ticket` | <https://queue-storm-7vjq.vercel.app/sort-ticket> |

The FastAPI backend and the React dashboard are both served from the
same origin at `https://queue-storm-7vjq.vercel.app`. The frontend
reads `VITE_API_BASE` from `App/frontend/.env` and points at this host
at build time.

## Stack

| Layer    | Tech                                             |
| -------- | ------------------------------------------------ |
| Backend  | Python 3.11+ · FastAPI · Pydantic · pytest      |
| Frontend | Vite · React 18 · TypeScript · Tailwind CSS      |
| Hosting  | Vercel (single HTTPS endpoint serves both API and built frontend) |

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
│   ├── .env                 VITE_API_BASE → deployed backend URL
│   ├── .env.example         template (safe to commit)
│   ├── package.json
│   └── README.md
├── docker-compose.yml       Optional: spin up backend in a container
└── README.md                ← you are here
```

## Endpoints

### `GET /health`

```bash
curl https://queue-storm-7vjq.vercel.app/health
```

```json
{ "status": "ok", "service": "queuestorm-warmup" }
```

### `POST /sort-ticket`

```bash
curl -X POST https://queue-storm-7vjq.vercel.app/sort-ticket \
  -H 'Content-Type: application/json' \
  -d '{
    "ticket_id": "T-001",
    "channel": "app",
    "locale": "en",
    "message": "I sent 3000 taka to wrong number this morning, please help"
  }'
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
  "confidence": 0.65
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
- http://localhost:8000/sort-ticket (POST)

### Frontend (dev mode — talks to local backend)

```bash
cd App/frontend
npm install
npm run dev
```

Open http://localhost:5173. With no `VITE_API_BASE` set, Vite proxies
`/sort-ticket` and `/health` to `http://localhost:8000`.

### Frontend (dev mode — talks to the live Vercel backend)

```bash
cd App/frontend
npm install
# .env already contains VITE_API_BASE=https://queue-storm-7vjq.vercel.app
npm run dev
```

The dev UI will POST directly to the Vercel deployment.

### Frontend (production build, served by FastAPI on a single host)

```bash
cd App/frontend
npm install
npm run build                # writes to App/frontend/dist
cd ../backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Now visit http://localhost:8000 — the React app loads from FastAPI
and `/health` and `/sort-ticket` are available on the same origin.
This is exactly how the Vercel deployment is configured.

### Frontend (production build deployed to a static host)

Build the bundle (`npm run build`) and upload `App/frontend/dist/`.
The bundle has `VITE_API_BASE` baked in from `.env`, so it will call
the configured backend host. To repoint, edit `App/frontend/.env`
and rebuild.

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

## Environment Variables

### Frontend (`App/frontend/.env`)

| Var              | Purpose                                                                 |
| ---------------- | ----------------------------------------------------------------------- |
| `VITE_API_BASE`  | Backend origin inlined at build time. Default: `https://queue-storm-7vjq.vercel.app`. Trailing slashes are stripped. |

`.env` is git-ignored; `.env.example` is the safe-to-commit template.

### Backend (`.env` or platform env vars)

| Var           | Default | Purpose                                  |
| ------------- | ------- | ---------------------------------------- |
| `PORT`        | `8000`  | Port for `uvicorn` to bind.              |
| `CORS_ORIGINS`| `*`     | Comma-separated origins or `*` for all.  |

## Safety

The grader will auto-fail any response whose `agent_summary` asks the
customer to share PIN, OTP, password, or full card number.

We defend against this in two layers:

1. The summary builder (`classifier._build_summary`) never produces
   such instructions — it only describes the situation.
2. `safety.scrub` runs as the **last** step before returning the
   response and strips any imperative "share/send/give/verify your X"
   phrasing, replacing it with a neutral safety line.

## Deployment (Vercel)

**Live URL:** <https://queue-storm-7vjq.vercel.app>

- **Build command:**
  ```bash
  cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt
  ```
- **Start command:**
  ```bash
  cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
- **Environment variables:** none required on the backend (optional: `CORS_ORIGINS`).
  The frontend `VITE_API_BASE` is baked in at build time from `App/frontend/.env`.

HTTPS is handled by Vercel automatically. The single URL exposes:

- `GET  /health`           — health probe
- `POST /sort-ticket`      — classification endpoint
- `GET  /`                 — React dashboard

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
