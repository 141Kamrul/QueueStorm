import type { Channel, Locale, SortTicketRequest } from "../types";
import { INPUT, INPUT_MONO } from "../styles";

interface Props {
  value: SortTicketRequest;
  onChange: (next: SortTicketRequest) => void;
  onSubmit: () => void;
  loading: boolean;
}

const CHANNELS: Array<{ value: Channel | ""; label: string }> = [
  { value: "", label: "(unspecified)" },
  { value: "app", label: "App" },
  { value: "sms", label: "SMS" },
  { value: "call_center", label: "Call Center" },
  { value: "merchant_portal", label: "Merchant Portal" },
];

const LOCALES: Array<{ value: Locale | ""; label: string }> = [
  { value: "", label: "(unspecified)" },
  { value: "en", label: "English (en)" },
  { value: "bn", label: "Bengali (bn)" },
  { value: "mixed", label: "Mixed" },
];

export default function TicketForm({ value, onChange, onSubmit, loading }: Props) {
  const set = <K extends keyof SortTicketRequest>(key: K, v: SortTicketRequest[K]) =>
    onChange({ ...value, [key]: v });

  return (
    <form
      className="flex h-full flex-col gap-4"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <div className="grid grid-cols-2 gap-3">
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-700">Ticket ID</span>
          <input
            className={INPUT_MONO}
            value={value.ticket_id}
            onChange={(e) => set("ticket_id", e.target.value)}
            placeholder="T-001"
            required
          />
        </label>
        <label className="flex flex-col gap-1 text-sm">
          <span className="font-medium text-slate-700">Channel</span>
          <select
            className={INPUT}
            value={value.channel ?? ""}
            onChange={(e) =>
              set("channel", (e.target.value || undefined) as Channel)
            }
          >
            {CHANNELS.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="flex flex-col gap-1 text-sm">
        <span className="font-medium text-slate-700">Locale</span>
        <select
          className={INPUT}
          value={value.locale ?? ""}
          onChange={(e) =>
            set("locale", (e.target.value || undefined) as Locale)
          }
        >
          {LOCALES.map((l) => (
            <option key={l.value} value={l.value}>
              {l.label}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-1 flex-col gap-1 text-sm">
        <span className="font-medium text-slate-700">Message</span>
        <textarea
          className={`min-h-[180px] flex-1 resize-none leading-relaxed ${INPUT}`}
          value={value.message}
          onChange={(e) => set("message", e.target.value)}
          placeholder="Paste the customer's complaint here..."
          required
        />
      </label>

      <button
        type="submit"
        disabled={loading || !value.ticket_id || !value.message}
        className="self-start rounded-md bg-bkash px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-bkash-dark disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Classifying…" : "Classify ticket"}
      </button>
    </form>
  );
}
