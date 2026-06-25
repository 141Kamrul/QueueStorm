# QueueStorm Warmup — Frontend

React + Vite + TypeScript + Tailwind dashboard for the ticket classifier.

## Quick Start (Dev)

```bash
cd App/frontend
npm install
npm run dev
```

The dev server runs on http://localhost:5173 and proxies `/api/*` to the
FastAPI backend on http://localhost:8000. Make sure the backend is running
first (`cd ../backend && uvicorn app.main:app --reload`).

## Production Build

```bash
npm run build
```

Outputs to `App/frontend/dist`. The FastAPI app automatically mounts this
folder at `/` so a single deploy serves both the UI and the API.

## Layout

- `src/App.tsx` — main layout, state, sample-case buttons
- `src/components/TicketForm.tsx` — input form (ticket_id, channel, locale, message)
- `src/components/ResultPanel.tsx` — pretty classification + raw JSON
- `src/components/SampleCases.tsx` — the 5 sample cases from Problem.txt
- `src/api.ts` — fetch wrapper for the backend
- `src/types.ts` — TypeScript types matching the backend Pydantic schemas

## Environment

No environment variables needed in the frontend. The API base is hard-coded
to `/api`, which Vite proxies to the backend in dev and resolves to the same
origin in production.