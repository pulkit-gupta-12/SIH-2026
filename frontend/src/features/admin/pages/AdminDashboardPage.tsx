/**
 * National Admin Dashboard Page (Steps H & I).
 * Route: /admin
 * Displays aggregate compliance KPIs, category/regional violation breakdowns,
 * officer leaderboard, and inspection priority weight configuration.
 */
import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { adminApi } from '../api';

export default function AdminDashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [riskEngineWeight, setRiskEngineWeight] = useState(0.5);
  const [complaintWeight, setComplaintWeight] = useState(0.3);
  const [ecommerceWeight, setEcommerceWeight] = useState(0.2);
  const [repeatMultiplier, setRepeatMultiplier] = useState(1.5);
  const [weightSaveMsg, setWeightSaveMsg] = useState('');
  const [adminSearch, setAdminSearch] = useState('');
  const [adminFilter, setAdminFilter] = useState('all');

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['admin-dashboard-summary'],
    queryFn: adminApi.getAdminDashboardSummary,
  });

  const { data: weightsConfig } = useQuery({
    queryKey: ['admin-inspection-weights'],
    queryFn: adminApi.getInspectionWeights,
  });

  useEffect(() => {
    if (weightsConfig) {
      const timer = setTimeout(() => {
        setRiskEngineWeight(weightsConfig.risk_engine_weight);
        setComplaintWeight(weightsConfig.complaint_weight);
        setEcommerceWeight(weightsConfig.ecommerce_weight);
        setRepeatMultiplier(weightsConfig.repeat_offense_multiplier);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [weightsConfig]);

  const updateWeightsMutation = useMutation({
    mutationFn: (payload: any) => adminApi.updateInspectionWeights(payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['admin-inspection-weights'], updated);
      setWeightSaveMsg('Inspection priority scoring weights saved successfully.');
      setTimeout(() => setWeightSaveMsg(''), 4000);
    },
  });

  const handleSaveWeights = (e: React.FormEvent) => {
    e.preventDefault();
    updateWeightsMutation.mutate({
      risk_engine_weight: parseFloat(riskEngineWeight.toString()),
      complaint_weight: parseFloat(complaintWeight.toString()),
      ecommerce_weight: parseFloat(ecommerceWeight.toString()),
      repeat_offense_multiplier: parseFloat(repeatMultiplier.toString()),
    });
  };

  const kpis = summary?.kpis;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-card p-6 border-l-4 border-indigo-500 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              National Command Console &middot; Phase 4.3
            </span>
            <span className="text-xs text-slate-400">Department of Consumer Affairs</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">Rule Engine Admin Dashboard</h1>
          <p className="text-sm text-slate-300 mt-0.5">
            Centralized policy oversight, automated rule drafting, and nationwide enforcement analytics.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/admin/rules/notifications')}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-amber-600 hover:bg-amber-500 text-white shadow-md transition-all cursor-pointer"
          >
            🔔 Amendment Notifications ({kpis?.new_notifications || 0})
          </button>
          <button
            onClick={() => navigate('/admin/rules')}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md transition-all cursor-pointer"
          >
            📜 Rule Repository
          </button>
        </div>
      </div>

      {/* Quick Search & Filter Controls */}
      <div className="glass-card p-4 rounded-2xl border border-slate-800 space-y-3">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-sm pointer-events-none">🔍</span>
            <input
              type="text"
              value={adminSearch}
              onChange={(e) => setAdminSearch(e.target.value)}
              placeholder="Search state divisions, product categories, or officers..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-black border border-slate-700 text-white placeholder-slate-400 text-sm focus:outline-none focus:border-indigo-500 transition-all font-mono search-input"
              style={{ backgroundColor: '#000000', color: '#ffffff' }}
            />
          </div>

          <div className="w-full sm:w-auto">
            <select
              value={adminFilter}
              onChange={(e) => setAdminFilter(e.target.value)}
              className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-black border border-slate-700 text-white text-sm focus:outline-none focus:border-indigo-500 transition-all dropdown-select"
              style={{ backgroundColor: '#000000', color: '#ffffff' }}
            >
              <option value="all" className="bg-black text-white">All Divisions & Categories</option>
              <option value="food" className="bg-black text-white">Food & Beverages</option>
              <option value="electronics" className="bg-black text-white">Electronics</option>
              <option value="general" className="bg-black text-white">General Goods</option>
              <option value="medical_device" className="bg-black text-white">Medical Devices</option>
              <option value="import" className="bg-black text-white">Imported Goods</option>
              <option value="ecommerce" className="bg-black text-white">E-Commerce</option>
            </select>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-5 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold uppercase text-slate-400">Active Live Rules</span>
          <div className="text-2xl md:text-3xl font-extrabold text-indigo-400">
            {summaryLoading ? '...' : kpis?.total_active_rules || 20}
          </div>
          <p className="text-[11px] text-slate-500">In-force Legal Metrology rules</p>
        </div>

        <div className="glass-card p-5 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold uppercase text-slate-400">Pending Rule Drafts</span>
          <div className="text-2xl md:text-3xl font-extrabold text-amber-400">
            {summaryLoading ? '...' : kpis?.pending_drafts || 0}
          </div>
          <p className="text-[11px] text-slate-500">Drafts awaiting approval</p>
        </div>

        <div className="glass-card p-5 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold uppercase text-slate-400">Enforcement Cases</span>
          <div className="text-2xl md:text-3xl font-extrabold text-rose-400">
            {summaryLoading ? '...' : kpis?.total_cases || 0}
          </div>
          <p className="text-[11px] text-slate-500">
            {kpis?.escalated_cases || 0} escalated to penalty
          </p>
        </div>

        <div className="glass-card p-5 border border-slate-800 space-y-1">
          <span className="text-xs font-semibold uppercase text-slate-400">National Compliance</span>
          <div className="text-2xl md:text-3xl font-extrabold text-emerald-400">
            {summaryLoading ? '...' : `${kpis?.national_compliance_rate || 88.5}%`}
          </div>
          <p className="text-[11px] text-slate-500">Aggregated across all states</p>
        </div>
      </div>

      {/* Breakdown: Violations by Category & Regional Map */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="glass-card p-5 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              Violations by Product Category (Step H)
            </h3>
            <span className="text-xs text-slate-400">All Active Checks</span>
          </div>

          <div className="space-y-3">
            {(summary?.violations_by_category || [])
              .filter((catItem) =>
                (adminFilter === 'all' || catItem.category.toLowerCase() === adminFilter.toLowerCase()) &&
                (!adminSearch || catItem.category.toLowerCase().includes(adminSearch.toLowerCase()))
              )
              .map((catItem) => (
              <div key={catItem.category} className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="capitalize text-slate-300">{catItem.category}</span>
                  <span className="font-mono text-slate-400">{catItem.violations} Violations</span>
                </div>
                <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="bg-indigo-500 h-full rounded-full"
                    style={{ width: `${Math.min(100, catItem.violations * 5 + 10)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Violations by Region / State */}
        <div className="glass-card p-5 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              Regional Enforcement & State Jurisdiction
            </h3>
            <span className="text-xs text-slate-400">State Division</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-500 border-b border-slate-800">
                <tr>
                  <th className="pb-2">State / Division</th>
                  <th className="pb-2">Complaints</th>
                  <th className="pb-2">Inspections</th>
                  <th className="pb-2 text-right">Compliance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/50">
                {(summary?.violations_by_region || [])
                  .filter((reg) => !adminSearch || reg.region.toLowerCase().includes(adminSearch.toLowerCase()))
                  .map((reg) => (
                  <tr key={reg.region}>
                    <td className="py-2.5 font-medium text-slate-200">{reg.region}</td>
                    <td className="py-2.5 text-slate-400 font-mono">{reg.complaints}</td>
                    <td className="py-2.5 text-slate-400 font-mono">{reg.inspections}</td>
                    <td className="py-2.5 text-right font-mono text-emerald-400">
                      {reg.compliance_rate}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Officer Performance Leaderboard & Inspection Weight Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Officer Performance Leaderboard */}
        <div className="glass-card p-5 border border-slate-800 space-y-4">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
            Field Officer Enforcement Activity
          </h3>

          <div className="space-y-2">
            {(summary?.officer_performance || [])
              .filter((officer) =>
                !adminSearch ||
                officer.name.toLowerCase().includes(adminSearch.toLowerCase()) ||
                officer.username.toLowerCase().includes(adminSearch.toLowerCase())
              )
              .map((officer) => (
              <div
                key={officer.officer_id}
                className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs"
              >
                <div>
                  <p className="font-semibold text-white">{officer.name}</p>
                  <p className="text-[11px] text-slate-500 font-mono">@{officer.username}</p>
                </div>
                <div className="flex items-center gap-4 text-right">
                  <div>
                    <span className="text-[10px] uppercase text-slate-500 block">Scans</span>
                    <span className="font-mono text-slate-300">{officer.scans_conducted}</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-500 block">Cases</span>
                    <span className="font-mono text-rose-400">{officer.cases_opened}</span>
                  </div>
                  <div>
                    <span className="text-[10px] uppercase text-slate-500 block">Done</span>
                    <span className="font-mono text-emerald-400">{officer.inspections_completed}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step I: Inspection Priority Weight Adjuster */}
        <div className="glass-card p-5 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-amber-400 uppercase tracking-wider">
              Inspection Priority Adjustment &middot; Step I
            </h3>
            <span className="text-xs text-slate-400 font-mono">Risk Scoring Engine</span>
          </div>

          <p className="text-xs text-slate-400">
            Tune the weights feeding the automated field inspection risk queue and target prioritization.
          </p>

          {weightSaveMsg && (
            <div className="p-2.5 rounded-lg bg-emerald-950/40 border border-emerald-700 text-xs text-emerald-300">
              ✓ {weightSaveMsg}
            </div>
          )}

          <form onSubmit={handleSaveWeights} className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between mb-1 text-slate-300">
                <span>Risk Engine Weight: {riskEngineWeight}</span>
                <span className="text-slate-500">Historical violation patterns</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={riskEngineWeight}
                onChange={(e) => setRiskEngineWeight(parseFloat(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1 text-slate-300">
                <span>Citizen Complaint Weight: {complaintWeight}</span>
                <span className="text-slate-500">Public grievances & escalations</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={complaintWeight}
                onChange={(e) => setComplaintWeight(parseFloat(e.target.value))}
                className="w-full accent-amber-500"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1 text-slate-300">
                <span>E-Commerce Flag Weight: {ecommerceWeight}</span>
                <span className="text-slate-500">Digital catalog discrepancies</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={ecommerceWeight}
                onChange={(e) => setEcommerceWeight(parseFloat(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>

            <div className="flex justify-between items-center pt-2">
              <span className="text-[11px] text-slate-400">
                Repeat Offense Multiplier: <strong>{repeatMultiplier}x</strong>
              </span>
              <button
                type="submit"
                disabled={updateWeightsMutation.isPending}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-amber-600 hover:bg-amber-500 text-white cursor-pointer disabled:opacity-50"
              >
                {updateWeightsMutation.isPending ? 'Saving...' : 'Save Priority Weights'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
