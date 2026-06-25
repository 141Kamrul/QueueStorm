import type { CaseType, Channel, Locale, Severity } from "../types";

export interface Sample {
  id: string;
  label: string;
  ticket_id: string;
  message: string;
  channel: Channel;
  locale: Locale;
  expected: `${CaseType} / ${Severity}`;
}

export const SAMPLES: Sample[] = [
  {
    id: "s1",
    label: "Wrong transfer",
    ticket_id: "T-001",
    message: "I sent 3000 taka to wrong number this morning, please help me get it back",
    channel: "app",
    locale: "en",
    expected: "wrong_transfer / high",
  },
  {
    id: "s2",
    label: "Payment failed",
    ticket_id: "T-002",
    message: "Payment failed but balance deducted from my account",
    channel: "app",
    locale: "en",
    expected: "payment_failed / high",
  },
  {
    id: "s3",
    label: "Phishing",
    ticket_id: "T-003",
    message: "Someone called asking my OTP, is that bKash?",
    channel: "call_center",
    locale: "en",
    expected: "phishing_or_social_engineering / critical",
  },
  {
    id: "s4",
    label: "Refund",
    ticket_id: "T-004",
    message: "Please refund my last transaction, I changed my mind",
    channel: "app",
    locale: "en",
    expected: "refund_request / low",
  },
  {
    id: "s5",
    label: "Other",
    ticket_id: "T-005",
    message: "App crashed when I opened it",
    channel: "app",
    locale: "en",
    expected: "other / low",
  },
];

interface Props {
  onLoad: (s: Sample) => void;
}

export default function SampleCases({ onLoad }: Props) {
  return (
    <div className="flex flex-col gap-2">
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        Try a sample case
      </div>
      <div className="flex flex-wrap gap-2">
        {SAMPLES.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => onLoad(s)}
            className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 transition hover:border-bkash hover:text-bkash"
            title={`Expected: ${s.expected}`}
          >
            {s.label}
          </button>
        ))}
      </div>
    </div>
  );
}