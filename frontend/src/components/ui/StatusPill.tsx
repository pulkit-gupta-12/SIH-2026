export type VerdictOrStatus =
  | "compliant"
  | "non_compliant"
  | "needs_review"
  | "unknown"
  | "open"
  | "under_investigation"
  | "resolved"
  | "dismissed"
  | string;

const STYLES: Record<string, string> = {
  compliant: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  non_compliant: "bg-rose-500/15 text-rose-400 border-rose-500/30",
  needs_review: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  unknown: "bg-slate-500/15 text-slate-400 border-slate-500/30",
  open: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  under_investigation: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  resolved: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  dismissed: "bg-slate-500/15 text-slate-400 border-slate-500/30",
};

const LABELS: Record<string, string> = {
  compliant: "Compliant",
  non_compliant: "Non-Compliant",
  needs_review: "Needs Review",
  unknown: "Not Checked Yet",
  open: "Open",
  under_investigation: "Under Investigation",
  resolved: "Resolved",
  dismissed: "Dismissed",
};

export default function StatusPill({ verdict }: { verdict: VerdictOrStatus }) {
  const normalized = (verdict || "unknown").toLowerCase();
  const style = STYLES[normalized] ?? STYLES.unknown;
  const label = LABELS[normalized] ?? verdict.replace(/_/g, " ");

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold tracking-wide border shadow-sm ${style}`}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{
          backgroundColor:
            normalized === "compliant" || normalized === "resolved"
              ? "#10b981"
              : normalized === "non_compliant"
              ? "#f43f5e"
              : normalized === "needs_review"
              ? "#f59e0b"
              : normalized === "open"
              ? "#3b82f6"
              : normalized === "under_investigation"
              ? "#a855f7"
              : "#94a3b8",
        }}
      />
      {label}
    </span>
  );
}
