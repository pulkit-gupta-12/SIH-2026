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
    <div className="max-w-4xl mx-auto p-4 md:p-8 space-y-8 animate-fade-in">
      {/* Hero Welcome Card */}
      <div className="relative rounded-3xl p-6 md:p-8 overflow-hidden bg-gradient-to-br from-emerald-950/80 via-slate-900 to-slate-950 border border-emerald-500/20 shadow-2xl">
        <div className="absolute -right-6 -bottom-6 text-9xl opacity-10 select-none pointer-events-none">
          ⚖️
        </div>
        <div className="relative z-10 space-y-4 max-w-xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <span>🛡️ National Legal Metrology Platform</span>
          </div>
          <h1 className="text-2xl md:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Citizen Compliance Hub
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Verify MRP integrity, standard net weights, statutory manufacturer details, and report overcharging or deceptive declarations directly to state controllers.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <button
              onClick={() => navigate("/citizen/scan")}
              className="px-5 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 shadow-lg shadow-emerald-950/60 transition-all flex items-center gap-2"
            >
              <span>📷 Open Barcode Scanner</span>
            </button>
            <button
              onClick={() => navigate("/citizen/complaints")}
              className="px-5 py-3 rounded-xl font-semibold text-slate-200 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 transition-all flex items-center gap-2"
            >
              <span>📝 View My Complaints ({complaints.length})</span>
            </button>
          </div>
        </div>
      </div>

      {/* Quick Search & Category Dropdown */}
      <div className="glass-card p-4 rounded-2xl border border-slate-800 space-y-3">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm pointer-events-none">🔍</span>
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
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-black border border-slate-700 text-white placeholder-slate-400 text-sm focus:outline-none focus:border-emerald-500 transition-all font-mono search-input"
              style={{ backgroundColor: '#000000', color: '#ffffff' }}
            />
          </div>

          <div className="w-full sm:w-auto">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-black border border-slate-700 text-white text-sm focus:outline-none focus:border-emerald-500 transition-all dropdown-select"
              style={{ backgroundColor: '#000000', color: '#ffffff' }}
            >
              <option value="all" className="bg-black text-white">All Commodities</option>
              <option value="food" className="bg-black text-white">Food & Beverages</option>
              <option value="electronics" className="bg-black text-white">Electronics</option>
              <option value="general" className="bg-black text-white">General Goods</option>
              <option value="medical_device" className="bg-black text-white">Medical Devices</option>
              <option value="import" className="bg-black text-white">Imported Commodities</option>
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
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-all whitespace-nowrap shadow-md"
          >
            Check Now →
          </button>
        </div>
      </div>

      {/* Quick Access Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Quick Scan */}
        <div
          onClick={() => navigate("/citizen/scan")}
          className="glass-card p-6 rounded-2xl border border-slate-800 hover:border-emerald-500/40 cursor-pointer transition-all duration-200 group space-y-3"
        >
          <div className="w-12 h-12 rounded-xl bg-emerald-500/15 text-emerald-400 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
            🔍
          </div>
          <h3 className="font-bold text-base text-white group-hover:text-emerald-400 transition-colors">
            Scan & Check Product
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Instant barcode verification against pre-packaged commodities statutory rules.
          </p>
        </div>

        {/* Card 2: Report Grievance */}
        <div
          onClick={() => navigate("/citizen/complaint/new")}
          className="glass-card p-6 rounded-2xl border border-slate-800 hover:border-rose-500/40 cursor-pointer transition-all duration-200 group space-y-3"
        >
          <div className="w-12 h-12 rounded-xl bg-rose-500/15 text-rose-400 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
            🚩
          </div>
          <h3 className="font-bold text-base text-white group-hover:text-rose-400 transition-colors">
            File Metrology Complaint
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Report price tampering, expired dates, or missing declarations with photo proof.
          </p>
        </div>

        {/* Card 3: Track Status */}
        <div
          onClick={() => navigate("/citizen/complaints")}
          className="glass-card p-6 rounded-2xl border border-slate-800 hover:border-blue-500/40 cursor-pointer transition-all duration-200 group space-y-3"
        >
          <div className="w-12 h-12 rounded-xl bg-blue-500/15 text-blue-400 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
            📋
          </div>
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-base text-white group-hover:text-blue-400 transition-colors">
              Complaint Status
            </h3>
            {openComplaintsCount > 0 && (
              <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30">
                {openComplaintsCount} Active
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Track official inspection routing and resolution status for your filed grievances.
          </p>
        </div>
      </div>

      {/* Citizen Rights Notice */}
      <div className="glass-card p-6 rounded-2xl border border-slate-800/80 bg-slate-900/40 space-y-3">
        <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">
          Know Your Consumer Rights (Legal Metrology Rules, 2011)
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-slate-300">
          <div className="flex items-start gap-2">
            <span className="text-emerald-400">✓</span>
            <span>All pre-packaged commodities must clearly declare MRP inclusive of all taxes.</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-emerald-400">✓</span>
            <span>Net quantity, month & year of manufacture/import are mandatory.</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-emerald-400">✓</span>
            <span>Retailers cannot sell or charge above the printed Maximum Retail Price.</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-emerald-400">✓</span>
            <span>Consumer care details (name, address, email, phone) must be legible.</span>
          </div>
        </div>
      </div>
    </div>
  );
}
