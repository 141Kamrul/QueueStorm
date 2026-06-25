import type { SortTicketRequest, SortTicketResponse } from "./types";

// API base URL.
//
// Resolution order at build time (Vite inlines VITE_* env vars):
//   1. VITE_API_BASE from .env / .env.production / shell — used when the
//      frontend is hosted on a different origin from the API
//      (e.g. Vercel/Netlify/Cloudflare Pages pointing at a separate backend).
//   2. Empty string fallback — calls go to "/api/...", which in dev is
//      proxied by Vite to http://localhost:8000, and in a FastAPI-served
//      production build resolves to the same origin.
//
// Trailing slashes are stripped so `${API_BASE}/sort-ticket` always
// produces a well-formed URL.
const API_BASE = (import.meta.env.VITE_API_BASE ?? "").replace(/\/+$/, "");

export async function classify(
  payload: SortTicketRequest,
  signal?: AbortSignal,
): Promise<SortTicketResponse> {
  const res = await fetch(`${API_BASE}/api/sort-ticket`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = JSON.stringify(body.detail);
    } catch {
      // ignore
    }
    throw new Error(detail);
  }

  return res.json() as Promise<SortTicketResponse>;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/api/health`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}
