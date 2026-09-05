import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import StatusPill from "../../../components/ui/StatusPill";
import { getComplianceSnapshot, type ComplianceSnapshot } from "../api";

export default function ComplianceSnapshotPage() {
  const { productId } = useParams<{ productId: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const stateSnapshot = (location.state as ComplianceSnapshot) || null;

  const {
    data: snapshot,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["compliance-snapshot", productId],
    queryFn: () => getComplianceSnapshot(Number(productId)),
    initialData: stateSnapshot && stateSnapshot.product_id === Number(productId) ? stateSnapshot : undefined,
    enabled: !!productId,
  });

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto p-6 space-y-4 text-center py-20 animate-fade-in">
        <div className="w-10 h-10 border-3 border-green-200 border-t-emerald-500 rounded-full animate-spin mx-auto" />
        <p className="text-sm text-[var(--color-text-muted)]">Loading compliance snapshot...</p>
      </div>
    );
  }

  if (isError || !snapshot) {
    return (
      <div className="max-w-2xl mx-auto p-6 space-y-4">
        <div className="glass-card p-6 rounded-2xl text-center space-y-3">
          <div className="text-4xl">⚠️</div>
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Product Snapshot Not Found</h2>
          <p className="text-sm text-[var(--color-text-muted)]">
            We couldn&apos;t load the compliance report for this product.
          </p>
          <button
            onClick={() => navigate("/citizen/scan")}
            className="px-4 py-2 rounded-xl bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-[var(--color-text-primary)] text-sm font-semibold transition-all"
          >
            Back to Scan
          </button>
        </div>
      </div>
    );
  }

  const isCompliant = snapshot.verdict === "compliant";

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Top Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate("/citizen/scan")}
          className="flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
        >
          <span>←</span>
          <span>Back to Scanner</span>
        </button>
        <span className="text-xs text-[var(--color-text-muted)] font-mono">
          GTIN: {snapshot.gtin_barcode || "N/A"}
        </span>
      </div>

      {/* Main Verdict Card */}
      <div
        className={`glass-card p-6 rounded-2xl border ${
          isCompliant
            ? "border-green-200 bg-gradient-to-br from-emerald-950/30 via-slate-900/60 to-slate-950/80"
            : "border-red-200 bg-gradient-to-br from-rose-950/30 via-slate-900/60 to-slate-950/80"
        } shadow-xl space-y-4`}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[var(--color-border)]">
          <div className="space-y-1">
            <span className="text-xs font-semibold text-[var(--color-accent)] uppercase tracking-wider">
              {snapshot.brand_name || "Packaged Product"}
            </span>
            <h1 className="text-xl md:text-2xl font-bold text-[var(--color-text-primary)] tracking-tight">
              {snapshot.product_name}
            </h1>
          </div>
          <div>
            <StatusPill verdict={snapshot.verdict} />
          </div>
        </div>

        {/* Key Attributes */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-1 text-xs">
          <div className="p-3 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)]">
            <span className="text-[var(--color-text-muted)] block mb-1">Status</span>
            <span className="font-semibold text-[var(--color-text-primary)] capitalize">
              {snapshot.has_been_scanned ? "Verified in Registry" : "First Scan"}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)]">
            <span className="text-[var(--color-text-muted)] block mb-1">Violations Found</span>
            <span
              className={`font-semibold ${
                snapshot.violation_count === 0 ? "text-[var(--color-accent)]" : "text-red-600"
              }`}
            >
              {snapshot.violation_count} Issue{snapshot.violation_count === 1 ? "" : "s"}
            </span>
          </div>
          <div className="p-3 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] col-span-2 sm:col-span-1">
            <span className="text-[var(--color-text-muted)] block mb-1">Last Checked</span>
            <span className="font-semibold text-[var(--color-text-secondary)]">
              {snapshot.last_checked_at
                ? new Date(snapshot.last_checked_at).toLocaleDateString("en-IN", {
                    day: "numeric",
                    month: "short",
                    year: "numeric",
                  })
                : "Just now"}
            </span>
          </div>
        </div>
      </div>

      {/* Compliance Verdict Summary */}
      {isCompliant ? (
        <div className="p-4 rounded-2xl bg-[var(--color-accent)]/10 border border-green-300/20 text-[var(--color-accent)] text-sm flex items-start gap-3">
          <span className="text-xl mt-0.5">✅</span>
          <div className="space-y-0.5">
            <div className="font-semibold text-emerald-200">
              Fully Compliant with Legal Metrology (Packaged Commodities) Rules
            </div>
            <div className="text-xs text-[var(--color-accent)]/80 leading-relaxed">
              All mandatory declarations (MRP, Net Quantity, Manufacturer Address, Consumer Care, and Dates) meet regulatory requirements.
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center justify-between px-1">
            <h2 className="text-sm font-semibold text-red-600 uppercase tracking-wider">
              Flagged Declarations & Violations ({snapshot.violation_count})
            </h2>
            <span className="text-xs text-[var(--color-text-muted)]">Legal Metrology Act, 2009</span>
          </div>

          <div className="space-y-2.5">
            {snapshot.violations.map((v, idx) => (
              <div
                key={idx}
                className="glass-card p-4 rounded-xl border border-rose-500/20 bg-rose-950/10 space-y-2"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-red-50 text-red-600 border border-red-200">
                    {v.rule_code || `RULE #${v.rule_id}`}
                  </span>
                  {v.is_first_time !== null && v.is_first_time !== undefined && (
                    <span
                      className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                        v.is_first_time
                          ? "bg-amber-50 text-amber-600 border border-amber-200"
                          : "bg-red-50 text-red-600 border border-red-200"
                      }`}
                    >
                      {v.is_first_time ? "1st Offense Notice" : "Repeat Violation"}
                    </span>
                  )}
                </div>

                <p className="text-sm text-[var(--color-text-primary)] font-medium">
                  {v.description || "Declaration does not comply with statutory requirements."}
                </p>

                <div className="text-xs text-[var(--color-text-muted)] flex flex-wrap gap-x-3 gap-y-1 pt-1 border-t border-[var(--color-border)]">
                  {v.section_ref && <span>Section: {v.section_ref}</span>}
                  {v.field && <span className="capitalize">Field: {v.field.replace(/_/g, " ")}</span>}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
        <button
          onClick={() => navigate(`/citizen/product/${snapshot.product_id}`)}
          className="w-full py-3 px-4 rounded-xl text-sm font-semibold bg-[var(--color-surface-tertiary)] hover:bg-gray-100 text-[var(--color-text-primary)] border border-[var(--color-border)] transition-all flex items-center justify-center gap-2"
        >
          <span>📋 View Full Product Info</span>
        </button>

        <button
          onClick={() =>
            navigate(`/citizen/complaint/new`, {
              state: {
                productId: snapshot.product_id,
                productName: snapshot.product_name,
                brandName: snapshot.brand_name,
                barcode: snapshot.gtin_barcode,
              },
            })
          }
          className="w-full py-3 px-4 rounded-xl text-sm font-semibold bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-[var(--color-text-primary)] shadow-lg shadow-emerald-950/40 transition-all flex items-center justify-center gap-2"
        >
          <span>🚩 Report a Problem / File Complaint</span>
        </button>
      </div>
    </div>
  );
}
