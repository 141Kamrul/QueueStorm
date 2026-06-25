import type { SortTicketRequest, SortTicketResponse } from "./types";

// In dev, Vite proxies /api -> http://localhost:8000.
// In production, the FastAPI app serves the built bundle, so /api/sort-ticket
// resolves to the same origin.
const API_BASE = "/api";

export async function classify(
  payload: SortTicketRequest,
  signal?: AbortSignal,
): Promise<SortTicketResponse> {
  const res = await fetch(`${API_BASE}/sort-ticket`, {
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
    const res = await fetch(`${API_BASE}/health`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}
