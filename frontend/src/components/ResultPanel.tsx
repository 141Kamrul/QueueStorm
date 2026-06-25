import type { SortTicketResponse } from "../types";
import { EMPTY_STATE } from "../styles";

const SEVERITY_STYLES: Record<SortTicketResponse["severity"], string> = {
  low: "bg-slate-100 text-slate-700 ring-slate-200",
  medium: "bg-blue-100 text-blue-800 ring-blue-200",
  high: "bg-orange-100 text-orange-800 ring-orange-200",
  critical: "bg-red-100 text-red-800 ring-red-200",
};

const CASE_LABEL: Record<SortTicketResponse["case_type"], string> = {
  wrong_transfer: "Wrong transfer",
  payment_failed: "Payment failed",
  refund_request: "Refund request",
  phishing_or_social_engineering: "Phishing / social engineering",
  other: "Other",
};

const DEPARTMENT_LABEL: Record<SortTicketResponse["department"], string> = {
  customer_support: "Customer support",
  dispute_resolution: "Dispute resolution",
  payments_ops: "Payments ops",
  fraud_risk: "Fraud risk",
};

interface Props {
  result: SortTicketResponse | null;
  raw: string;
  loading: boolean;
  error: string | null;
}

export default function ResultPanel({ result, raw, loading, error }: Props) {
  return (
    <div className="flex h-full flex-col gap-4">
      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading && !result && (
        <div className={EMPTY_STATE}>Classifying ticket…</div>
      )}

      {result && (
        <>
          {result.human_review_required && (
            <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm font-semibold text-red-800">
              ⚠ Human review required — escalate immediately.
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <Field label="Case type" value={CASE_LABEL[result.case_type]} />
            <Field
              label="Severity"
              value={
                <span
                  className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${SEVERITY_STYLES[result.severity]}`}
                >
                  {result.severity.toUpperCase()}
                </span>
              }
            />
            <Field label="Department" value={DEPARTMENT_LABEL[result.department]} />
            <Field
              label="Confidence"
              value={
                <span className="font-mono text-sm">
                  {(result.confidence * 100).toFixed(0)}%
                </span>
              }
            />
          </div>

          <div className="rounded-md border border-slate-200 bg-white p-3">
            <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
              Agent summary
            </div>
            <p className="text-sm leading-relaxed text-slate-800">
              {result.agent_summary}
            </p>
          </div>

          <details className="rounded-md border border-slate-200 bg-slate-50">
            <summary className="cursor-pointer select-none px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-600">
              Raw JSON response
            </summary>
            <pre className="overflow-x-auto border-t border-slate-200 bg-slate-900 p-3 text-xs leading-relaxed text-slate-100">
              {raw}
            </pre>
          </details>
        </>
      )}

      {!loading && !result && !error && (
        <div className={`${EMPTY_STATE} p-6 text-center`}>
          Submit a ticket to see the classification here.
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md border border-slate-200 bg-white p-3">
      <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="text-sm font-medium text-slate-900">{value}</div>
    </div>
  );
}
