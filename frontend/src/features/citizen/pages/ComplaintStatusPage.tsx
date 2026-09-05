import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMyComplaints, type Complaint } from "../api";
import StatusPill from "../../../components/ui/StatusPill";

export default function ComplaintStatusPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

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

  const filteredComplaints = complaints.filter((c: Complaint) => {
    const matchesSearch =
      !searchTerm ||
      (c.product_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.brand_name || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.description || "").toLowerCase().includes(searchTerm.toLowerCase()) ||
      `CMP-${String(c.id).padStart(5, "0")}`.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === "all" || c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <div className="max-w-3xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] tracking-tight">
            My Filed Complaints
          </h1>
          <p className="text-xs sm:text-sm text-[var(--color-text-muted)]">
            Track status, state officer routing, and investigation outcomes.
          </p>
        </div>
        <button
          onClick={() => navigate("/citizen/complaint/new")}
          className="px-4 py-2.5 rounded-xl text-sm font-semibold bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 text-[var(--color-text-primary)] shadow-lg shadow-emerald-950/40 transition-all flex items-center gap-1.5 self-start sm:self-auto"
        >
          <span>+ File New Complaint</span>
        </button>
      </div>

      {/* Search & Status Filter */}
      {complaints.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="sm:col-span-2 relative">
            <input
              type="text"
              placeholder="Search complaints by product, brand, or CMP ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] text-sm focus:outline-none focus:border-[var(--color-accent)]"
              style={{ backgroundColor: 'var(--color-surface-tertiary)', color: 'var(--color-text-primary)' }}
            />
          </div>
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:border-[var(--color-accent)]"
              style={{ backgroundColor: 'var(--color-surface-tertiary)', color: 'var(--color-text-primary)' }}
            >
              <option value="all" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">All Statuses ({complaints.length})</option>
              <option value="open" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Open</option>
              <option value="under_investigation" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Under Investigation</option>
              <option value="resolved" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Resolved</option>
              <option value="dismissed" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Dismissed</option>
            </select>
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="glass-card p-12 text-center space-y-3 rounded-2xl">
          <div className="w-8 h-8 border-3 border-green-200 border-t-emerald-500 rounded-full animate-spin mx-auto" />
          <p className="text-sm text-[var(--color-text-muted)]">Retrieving your complaint records...</p>
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="glass-card p-6 text-center space-y-3 rounded-2xl border border-red-200">
          <p className="text-sm text-red-600">Failed to load complaints.</p>
          <button
            onClick={() => refetch()}
            className="px-4 py-2 rounded-xl bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)] text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && complaints.length === 0 && (
        <div className="glass-card p-12 text-center rounded-2xl space-y-4 border border-[var(--color-border)]">
          <div className="text-5xl opacity-40">📝</div>
          <div className="space-y-1">
            <h2 className="text-base font-semibold text-[var(--color-text-primary)]">No Complaints Filed Yet</h2>
            <p className="text-xs text-[var(--color-text-muted)] max-w-sm mx-auto">
              Whenever you notice overcharging or non-compliant packaging in stores, scan the barcode and report it here.
            </p>
          </div>
          <button
            onClick={() => navigate("/citizen/scan")}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-[var(--color-text-primary)] transition-all shadow-md"
          >
            Scan a Product Now
          </button>
        </div>
      )}

      {/* Filtered Empty State */}
      {!isLoading && complaints.length > 0 && filteredComplaints.length === 0 && (
        <div className="glass-card p-8 text-center rounded-2xl space-y-2 border border-[var(--color-border)]">
          <p className="text-sm text-[var(--color-text-secondary)]">No complaints matching your search filter.</p>
          <button
            onClick={() => { setSearchTerm(''); setStatusFilter('all'); }}
            className="text-xs text-[var(--color-accent)] underline font-medium"
          >
            Clear filters
          </button>
        </div>
      )}

      {/* Complaints List */}
      {!isLoading && filteredComplaints.length > 0 && (
        <div className="space-y-4">
          {filteredComplaints.map((c: Complaint) => (
            <div
              key={c.id}
              className="glass-card p-5 rounded-2xl border border-[var(--color-border)] hover:border-[var(--color-accent)] transition-all space-y-3"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-[var(--color-border)]">
                <div className="flex items-center gap-2.5">
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-[var(--color-surface-tertiary)] text-[var(--color-accent)] border border-[var(--color-border)]">
                    CMP-{String(c.id).padStart(5, "0")}
                  </span>
                  <span className="text-xs text-[var(--color-text-muted)]">
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
                <div className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)]">
                  <span>📦 {c.product_name || `Product #${c.product}`}</span>
                  {c.brand_name && (
                    <span className="text-xs px-2 py-0.5 rounded bg-green-50 text-[var(--color-accent)] border border-green-200">
                      {c.brand_name}
                    </span>
                  )}
                </div>
                <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed bg-[var(--color-surface-tertiary)] p-3 rounded-xl border border-[var(--color-border)]">
                  {c.description}
                </p>
              </div>

              {/* Routing and Location Metadata */}
              <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-xs text-[var(--color-text-muted)]">
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
                  className="text-[var(--color-accent)] hover:text-[var(--color-accent)] font-medium text-xs flex items-center gap-1"
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
