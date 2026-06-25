# QueueStorm Warmup — Frontend

React + Vite + TypeScript + Tailwind dashboard for the ticket classifier.

**Live deployment:** <https://queue-storm-7vjq.vercel.app>

## Quick Start (Dev — talks to local backend)

```bash
cd App/frontend
npm install
npm run dev
```

The dev server runs on http://localhost:5173 and proxies `/sort-ticket`
and `/health` to the FastAPI backend on http://localhost:8000. Make
sure the backend is running first (`cd ../backend && uvicorn
app.main:app --reload`).

## Quick Start (Dev — talks to the live Vercel backend)

```bash
cd App/frontend
npm install
npm run dev
```

`App/frontend/.env` already sets `VITE_API_BASE=https://queue-storm-7vjq.vercel.app`,
so the dev UI calls the deployed backend directly — no local FastAPI
needed.

## Production Build

```bash
npm run build
```

Outputs to `App/frontend/dist`. Two deployment options:

1. **Single-host (recommended).** Let FastAPI serve the bundle by
   placing `dist/` next to `backend/` and starting `uvicorn` normally.
   The FastAPI app mounts `dist/` at `/` so one URL hosts both the UI
   and the API. This is exactly how the Vercel deployment is set up.
2. **Static host + separate API.** Upload `dist/` to a static host
   (Vercel, Netlify, Cloudflare Pages). The bundle has
   `VITE_API_BASE` baked in from `.env`, so it calls the configured
   backend origin.

## Environment Variables

The frontend reads **one** environment variable, baked in at build time:

| Var              | Purpose                                                                                |
| ---------------- | -------------------------------------------------------------------------------------- |
| `VITE_API_BASE`  | Backend origin. Trailing slashes are stripped. Default in `.env`: `https://queue-storm-7vjq.vercel.app`. |

- `.env` — active config (git-ignored)
- `.env.example` — committed template

To repoint the bundle, edit `.env` (or set `VITE_API_BASE` in your
deployment platform) and rebuild.

## Layout

- `src/App.tsx` — main layout, state, sample-case buttons
- `src/components/TicketForm.tsx` — input form (ticket_id, channel, locale, message)
- `src/components/ResultPanel.tsx` — pretty classification + raw JSON
- `src/components/SampleCases.tsx` — the 5 sample cases from Problem.txt
- `src/api.ts` — fetch wrapper for the backend (reads `VITE_API_BASE`)
- `src/types.ts` — TypeScript types matching the backend Pydantic schemas
- `src/styles.ts` — shared Tailwind class strings
- `src/vite-env.d.ts` — `import.meta.env` type declarations