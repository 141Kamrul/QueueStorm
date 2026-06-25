import { useEffect, useRef, useState } from "react";
import TicketForm from "./components/TicketForm";
import ResultPanel from "./components/ResultPanel";
import SampleCases from "./components/SampleCases";
import { checkHealth, classify } from "./api";
import { PANEL } from "./styles";
import type { Sample } from "./components/SampleCases";
import type { SortTicketRequest, SortTicketResponse } from "./types";

const DEFAULT_TICKET: SortTicketRequest = {
  ticket_id: "T-001",
  channel: "app",
  locale: "en",
  message: "",
};

export default function App() {
  const [ticket, setTicket] = useState<SortTicketRequest>(DEFAULT_TICKET);
  const [result, setResult] = useState<SortTicketResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [healthOk, setHealthOk] = useState<boolean | null>(null);

  // Aborts in-flight requests so a fast double-submit can't race.
  const inflight = useRef<AbortController | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const ok = await checkHealth();
      if (!cancelled) setHealthOk(ok);
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const onSubmit = async () => {
    inflight.current?.abort();
    const controller = new AbortController();
    inflight.current = controller;

    setLoading(true);
    setError(null);
    try {
      const data = await classify(ticket, controller.signal);
      setResult(data);
    } catch (e) {
      if ((e as { name?: string })?.name === "AbortError") return;
      setError(e instanceof Error ? e.message : String(e));
      setResult(null);
    } finally {
      if (inflight.current === controller) {
        inflight.current = null;
        setLoading(false);
      }
    }
  };

  const loadSample = (s: Sample) => {
    setTicket({
      ticket_id: s.ticket_id,
      channel: s.channel,
      locale: s.locale,
      message: s.message,
    });
  };

  const raw = result ? JSON.stringify(result, null, 2) : "";

  return (
    <div className="mx-auto flex min-h-screen max-w-7xl flex-col gap-4 p-4 lg:p-6">
      <header className={`flex items-center justify-between ${PANEL}`}>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-bkash text-lg font-extrabold text-white">
            Q
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900">QueueStorm Warmup</h1>
            <p className="text-xs text-slate-500">
              bKash SUST CSE Carnival 2026 — Mock Preliminary
            </p>
          </div>
        </div>
        <HealthBadge ok={healthOk} />
      </header>

      <SampleCases onLoad={loadSample} />

      <main className="grid flex-1 gap-4 lg:grid-cols-2">
        <section className={PANEL}>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Ticket
          </h2>
          <TicketForm
            value={ticket}
            onChange={setTicket}
            onSubmit={onSubmit}
            loading={loading}
          />
        </section>

        <section className={PANEL}>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Classification
          </h2>
          <ResultPanel
            result={result}
            raw={raw}
            loading={loading}
            error={error}
          />
        </section>
      </main>

      <footer className="text-center text-xs text-slate-400">
        Rules-based classifier · No LLM · Built for the SUST mock preliminary round.
      </footer>
    </div>
  );
}

function HealthBadge({ ok }: { ok: boolean | null }) {
  if (ok === null) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-500">
        <span className="h-2 w-2 rounded-full bg-slate-300" />
        Checking…
      </span>
    );
  }
  if (ok) {
    return (
      <span className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        /health OK
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700">
      <span className="h-2 w-2 rounded-full bg-red-500" />
      /health unreachable
    </span>
  );
}
