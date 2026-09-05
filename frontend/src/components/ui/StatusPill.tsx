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
  compliant: "bg-green-50 text-green-700 border-green-200",
  non_compliant: "bg-red-50 text-red-700 border-red-200",
  needs_review: "bg-amber-50 text-amber-700 border-amber-200",
  unknown: "bg-gray-50 text-gray-600 border-gray-200",
  open: "bg-blue-50 text-blue-700 border-blue-200",
  under_investigation: "bg-purple-50 text-purple-700 border-purple-200",
  resolved: "bg-green-50 text-green-700 border-green-200",
  dismissed: "bg-gray-50 text-gray-600 border-gray-200",
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

const DOT_COLORS: Record<string, string> = {
  compliant: "#16a34a",
  non_compliant: "#dc2626",
  needs_review: "#d97706",
  unknown: "#6b7280",
  open: "#2563eb",
  under_investigation: "#9333ea",
  resolved: "#16a34a",
  dismissed: "#6b7280",
};

export default function StatusPill({ verdict }: { verdict: VerdictOrStatus }) {
  const normalized = (verdict || "unknown").toLowerCase();
  const style = STYLES[normalized] ?? STYLES.unknown;
  const label = LABELS[normalized] ?? verdict.replace(/_/g, " ");
  const dotColor = DOT_COLORS[normalized] ?? "#6b7280";

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold tracking-wide border ${style}`}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: dotColor }}
      />
      {label}
    </span>
  );
}
