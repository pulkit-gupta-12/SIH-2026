import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMyComplaints, type Complaint } from "../api";
import StatusPill from "../../../components/ui/StatusPill";

export default function ComplaintStatusPage() {
  const navigate = useNavigate();

  const {
    data: complaints = [],
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ["my-complaints"],
    queryFn: getMyComplaints,
    staleTime: 15_000,
  });

  return (
    <div className="max-w-3xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            My Filed Complaints
          </h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Track status, state officer routing, and investigation outcomes.
          </p>
        </div>
        <button
          onClick={() => navigate("/citizen/complaint/new")}
          className="px-4 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-white shadow-lg shadow-emerald-950/40 transition-all flex items-center gap-1.5 self-start sm:self-auto"
        >
          <span>+ File New Complaint</span>
        </button>
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="glass-card p-12 text-center space-y-3 rounded-2xl">
          <div className="w-8 h-8 border-3 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-400">Retrieving your complaint records...</p>
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="glass-card p-6 text-center space-y-3 rounded-2xl border border-rose-500/30">
          <p className="text-sm text-rose-300">Failed to load complaints.</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 rounded-xl bg-slate-800 text-slate-200 text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && complaints.length === 0 && (
        <div className="glass-card p-12 text-center rounded-2xl space-y-4 border border-slate-800">
          <div className="text-5xl opacity-40">📝</div>
          <div className="space-y-1">
            <h2 className="text-base font-semibold text-white">No Complaints Filed Yet</h2>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              Whenever you notice overcharging or non-compliant packaging in stores, scan the barcode and report it here.
            </p>
          </div>
          <button
            onClick={() => navigate("/citizen/scan")}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md"
          >
            Scan a Product Now
          </button>
        </div>
      )}

      {/* Complaints List */}
      {!isLoading && complaints.length > 0 && (
        <div className="space-y-4">
          {complaints.map((c: Complaint) => (
            <div
              key={c.id}
              className="glass-card p-5 rounded-2xl border border-slate-800/80 hover:border-emerald-500/30 transition-all space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-800">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-800 text-emerald-400 border border-slate-700">
                    CMP-{String(c.id).padStart(5, "0")}
                  </span>
                  <span className="text-xs text-slate-400">
                    {new Date(c.created_at).toLocaleDateString("en-IN", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
                <div>
                  <StatusPill verdict={c.status} />
                </div>
              </div>

              {/* Product Context */}
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm font-semibold text-white">
                  <span>📦 {c.product_name || `Product #${c.product}`}</span>
                  {c.brand_name && (
                    <span className="text-xs px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-500/30">
                      {c.brand_name}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/50 p-3 rounded-xl border border-slate-800">
                  {c.description}
                </p>
              </div>

              {/* Routing and Location Metadata */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-xs text-slate-400">
                <div className="flex items-center gap-3">
                  {c.location && (
                    <span className="flex items-center gap-1">
                      <span>📍</span>
                      <span>{c.location}</span>
                    </span>
                  )}
                  {c.routed_to_state && (
                    <span className="flex items-center gap-1">
                      <span>🏛️</span>
                      <span>State: {c.routed_to_state}</span>
                    </span>
                  )}
                </div>
                <button
                  onClick={() => navigate(`/citizen/product/${c.product}/snapshot`)}
                  className="text-emerald-400 hover:text-emerald-300 font-medium text-xs flex items-center gap-1"
                >
                  View Product Snapshot →
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
