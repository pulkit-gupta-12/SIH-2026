import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getMyComplaints } from "../api";

export default function CitizenDashboardPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  const { data: complaints = [] } = useQuery({

    queryKey: ["my-complaints"],
    queryFn: getMyComplaints,
    staleTime: 30_000,
  });

  const openComplaintsCount = complaints.filter(
    (c) => c.status === "open" || c.status === "under_investigation"
  ).length;

  return (
    <div className="max-w-4xl mx-auto p-4 md:p-8 space-y-6 animate-fade-in">
      {/* Hero Welcome Card */}
      <div className="glass-card card-accent-left p-6 md:p-8">
        <div className="space-y-4 max-w-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
            <span>🛡️ National Legal Metrology Platform</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text-primary)] tracking-tight leading-tight">
            Citizen Compliance Hub
          </h1>
          <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
            Verify MRP integrity, standard net weights, statutory manufacturer details, and report overcharging or deceptive declarations directly to state controllers.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <button
              onClick={() => navigate("/citizen/scan")}
              className="px-5 py-3 rounded-lg font-semibold text-[var(--color-text-primary)] transition-colors flex items-center gap-2"
              style={{ background: 'linear-gradient(135deg, #e8730c, #d4670a)' }}
            >
              <span>📷 Open barcode scanner</span>
            </button>
            <button
              onClick={() => navigate("/citizen/complaints")}
              className="px-5 py-3 rounded-lg font-semibold text-[var(--color-text-secondary)] bg-[var(--color-surface-tertiary)] hover:bg-gray-200 border border-[var(--color-border)] transition-colors flex items-center gap-2"
            >
              <span>📝 View my complaints ({complaints.length})</span>
            </button>
          </div>
        </div>
      </div>

      {/* Quick Search & Category Dropdown */}
      <div className="glass-card p-4 space-y-3">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] text-sm pointer-events-none">🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && searchQuery.trim()) {
                  navigate(`/citizen/scan?barcode=${encodeURIComponent(searchQuery.trim())}&category=${selectedCategory}`);
                }
              }}
              placeholder="Search product barcode (GTIN) or brand to verify..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors font-mono"
            />
          </div>

          <div className="w-full sm:w-auto">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
            >
              <option value="all">All Commodities</option>
              <option value="food">Food & Beverages</option>
              <option value="electronics">Electronics</option>
              <option value="general">General Goods</option>
              <option value="medical_device">Medical Devices</option>
              <option value="import">Imported Commodities</option>
            </select>
          </div>

          <button
            type="button"
            onClick={() => {
              if (searchQuery.trim()) {
                navigate(`/citizen/scan?barcode=${encodeURIComponent(searchQuery.trim())}&category=${selectedCategory}`);
              } else {
                navigate('/citizen/scan');
              }
            }}
            className="w-full sm:w-auto px-5 py-2.5 rounded-lg text-sm font-semibold text-[var(--color-text-primary)] transition-colors whitespace-nowrap shadow-sm"
            style={{ background: 'var(--color-accent)' }}
          >
            Check now
          </button>
        </div>
      </div>

      {/* Quick Access Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Quick Scan */}
        <div
          onClick={() => navigate("/citizen/scan")}
          className="glass-card p-6 hover:border-[var(--color-accent)] cursor-pointer transition-all duration-150 group space-y-3 hover:shadow-md hover:-translate-y-px"
        >
          <div className="w-12 h-12 rounded-lg bg-[var(--color-accent-subtle)] text-[var(--color-accent)] flex items-center justify-center text-2xl group-hover:scale-105 transition-transform">
            🔍
          </div>
          <h3 className="font-bold text-base text-[var(--color-text-primary)] group-hover:text-[var(--color-accent)] transition-colors">
            Scan and check product
          </h3>
          <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
            Instant barcode verification against pre-packaged commodities statutory rules.
          </p>
        </div>

        {/* Card 2: Report Grievance */}
        <div
          onClick={() => navigate("/citizen/complaint/new")}
          className="glass-card p-6 hover:border-red-300 cursor-pointer transition-all duration-150 group space-y-3 hover:shadow-md hover:-translate-y-px"
        >
          <div className="w-12 h-12 rounded-lg bg-red-50 text-red-600 flex items-center justify-center text-2xl group-hover:scale-105 transition-transform">
            🚩
          </div>
          <h3 className="font-bold text-base text-[var(--color-text-primary)] group-hover:text-red-600 transition-colors">
            File metrology complaint
          </h3>
          <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
            Report price tampering, expired dates, or missing declarations with photo proof.
          </p>
        </div>

        {/* Card 3: Track Status */}
        <div
          onClick={() => navigate("/citizen/complaints")}
          className="glass-card p-6 hover:border-blue-300 cursor-pointer transition-all duration-150 group space-y-3 hover:shadow-md hover:-translate-y-px"
        >
          <div className="w-12 h-12 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center text-2xl group-hover:scale-105 transition-transform">
            📋
          </div>
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-base text-[var(--color-text-primary)] group-hover:text-blue-600 transition-colors">
              Complaint status
            </h3>
            {openComplaintsCount > 0 && (
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-600 border border-blue-200">
                {openComplaintsCount} Active
              </span>
            )}
          </div>
          <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
            Track official inspection routing and resolution status for your filed grievances.
          </p>
        </div>
      </div>

      {/* Citizen Rights Notice */}
      <div className="glass-card p-6 space-y-3">
        <h4 className="text-xs font-bold text-[var(--color-accent)]">
          Know your consumer rights (Legal Metrology Rules, 2011)
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-[var(--color-text-secondary)]">
          <div className="flex items-start gap-2">
            <span className="text-green-600">✓</span>
            <span>All pre-packaged commodities must clearly declare MRP inclusive of all taxes.</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-600">✓</span>
            <span>Net quantity, month & year of manufacture/import are mandatory.</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-600">✓</span>
            <span>Retailers cannot sell or charge above the printed Maximum Retail Price.</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-green-600">✓</span>
            <span>Consumer care details (name, address, email, phone) must be legible.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
