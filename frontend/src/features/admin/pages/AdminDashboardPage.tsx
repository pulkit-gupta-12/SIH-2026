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
      <div className="glass-card card-accent-left p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
              National Command Console &middot; Phase 4.3
            </span>
            <span className="text-xs text-[var(--color-text-muted)]">Department of Consumer Affairs</span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mt-1">Rule Engine Admin Dashboard</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-0.5">
            Centralized policy oversight, automated rule drafting, and nationwide enforcement analytics.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/admin/rules/notifications')}
            className="px-4 py-2 rounded-lg text-xs font-semibold text-[var(--color-text-primary)] shadow-sm transition-colors cursor-pointer"
            style={{ background: 'var(--color-accent)' }}
          >
            🔔 Amendment notifications ({kpis?.new_notifications || 0})
          </button>
          <button
            onClick={() => navigate('/admin/rules')}
            className="px-4 py-2 rounded-lg text-xs font-semibold bg-[var(--color-surface-tertiary)] text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:bg-gray-200 transition-colors cursor-pointer"
          >
            📜 Rule repository
          </button>
        </div>
      </div>

      {/* Quick Search & Filter Controls */}
      <div className="glass-card p-4 space-y-3">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] text-sm pointer-events-none">🔍</span>
            <input
              type="text"
              value={adminSearch}
              onChange={(e) => setAdminSearch(e.target.value)}
              placeholder="Search state divisions, product categories, or officers..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors font-mono"
            />
          </div>

          <div className="w-full sm:w-auto">
            <select
              value={adminFilter}
              onChange={(e) => setAdminFilter(e.target.value)}
              className="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
            >
              <option value="all">All Divisions & Categories</option>
              <option value="food">Food & Beverages</option>
              <option value="electronics">Electronics</option>
              <option value="general">General Goods</option>
              <option value="medical_device">Medical Devices</option>
              <option value="import">Imported Goods</option>
              <option value="ecommerce">E-Commerce</option>
            </select>
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-5 space-y-1">
          <span className="text-xs font-semibold text-[var(--color-text-muted)]">Active live rules</span>
          <div className="text-2xl md:text-3xl font-bold text-[var(--color-accent)]">
            {summaryLoading ? '...' : kpis?.total_active_rules || 20}
          </div>
          <p className="text-[11px] text-[var(--color-text-muted)]">In-force Legal Metrology rules</p>
        </div>

        <div className="glass-card p-5 space-y-1">
          <span className="text-xs font-semibold text-[var(--color-text-muted)]">Pending rule drafts</span>
          <div className="text-2xl md:text-3xl font-bold text-amber-600">
            {summaryLoading ? '...' : kpis?.pending_drafts || 0}
          </div>
          <p className="text-[11px] text-[var(--color-text-muted)]">Drafts awaiting approval</p>
        </div>

        <div className="glass-card p-5 space-y-1">
          <span className="text-xs font-semibold text-[var(--color-text-muted)]">Enforcement cases</span>
          <div className="text-2xl md:text-3xl font-bold text-red-600">
            {summaryLoading ? '...' : kpis?.total_cases || 0}
          </div>
          <p className="text-[11px] text-[var(--color-text-muted)]">
            {kpis?.escalated_cases || 0} escalated to penalty
          </p>
        </div>

        <div className="glass-card p-5 space-y-1">
          <span className="text-xs font-semibold text-[var(--color-text-muted)]">National compliance</span>
          <div className="text-2xl md:text-3xl font-bold text-green-600">
            {summaryLoading ? '...' : `${kpis?.national_compliance_rate || 88.5}%`}
          </div>
          <p className="text-[11px] text-[var(--color-text-muted)]">Aggregated across all states</p>
        </div>
      </div>

      {/* Breakdown: Violations by Category & Regional Map */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-[var(--color-text-primary)]">
              Violations by product category (Step H)
            </h3>
            <span className="text-xs text-[var(--color-text-muted)]">All active checks</span>
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
                  <span className="capitalize text-[var(--color-text-secondary)]">{catItem.category}</span>
                  <span className="font-mono text-[var(--color-text-muted)]">{catItem.violations} Violations</span>
                </div>
                <div className="w-full h-2 rounded-full bg-[var(--color-surface-tertiary)] overflow-hidden">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(100, catItem.violations * 5 + 10)}%`,
                      background: 'var(--color-accent)',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Violations by Region / State */}
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-[var(--color-text-primary)]">
              Regional enforcement and state jurisdiction
            </h3>
            <span className="text-xs text-[var(--color-text-muted)]">State Division</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-[var(--color-text-muted)] border-b border-[var(--color-border)]">
                <tr>
                  <th className="pb-2">State / Division</th>
                  <th className="pb-2">Complaints</th>
                  <th className="pb-2">Inspections</th>
                  <th className="pb-2 text-right">Compliance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]">
                {(summary?.violations_by_region || [])
                  .filter((reg) => !adminSearch || reg.region.toLowerCase().includes(adminSearch.toLowerCase()))
                  .map((reg) => (
                  <tr key={reg.region}>
                    <td className="py-2.5 font-medium text-[var(--color-text-primary)]">{reg.region}</td>
                    <td className="py-2.5 text-[var(--color-text-muted)] font-mono">{reg.complaints}</td>
                    <td className="py-2.5 text-[var(--color-text-muted)] font-mono">{reg.inspections}</td>
                    <td className="py-2.5 text-right font-mono text-green-600">
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
        <div className="glass-card p-5 space-y-4">
          <h3 className="text-xs font-bold text-[var(--color-text-primary)]">
            Field officer enforcement activity
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
                className="p-3 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] flex items-center justify-between text-xs"
              >
                <div>
                  <p className="font-semibold text-[var(--color-text-primary)]">{officer.name}</p>
                  <p className="text-[11px] text-[var(--color-text-muted)] font-mono">@{officer.username}</p>
                </div>
                <div className="flex items-center gap-4 text-right">
                  <div>
                    <span className="text-[10px] text-[var(--color-text-muted)] block">Scans</span>
                    <span className="font-mono text-[var(--color-text-secondary)]">{officer.scans_conducted}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[var(--color-text-muted)] block">Cases</span>
                    <span className="font-mono text-red-600">{officer.cases_opened}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-[var(--color-text-muted)] block">Done</span>
                    <span className="font-mono text-green-600">{officer.inspections_completed}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Step I: Inspection Priority Weight Adjuster */}
        <div className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-[var(--color-accent)]">
              Inspection priority adjustment &middot; Step I
            </h3>
            <span className="text-xs text-[var(--color-text-muted)] font-mono">Risk Scoring Engine</span>
          </div>

          <p className="text-xs text-[var(--color-text-muted)]">
            Tune the weights feeding the automated field inspection risk queue and target prioritization.
          </p>

          {weightSaveMsg && (
            <div className="p-2.5 rounded-lg bg-green-50 border border-green-200 text-xs text-green-700">
              ✓ {weightSaveMsg}
            </div>
          )}

          <form onSubmit={handleSaveWeights} className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between mb-1 text-[var(--color-text-secondary)]">
                <span>Risk Engine Weight: {riskEngineWeight}</span>
                <span className="text-[var(--color-text-muted)]">Historical violation patterns</span>
              </div>
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                value={riskEngineWeight}
                onChange={(e) => setRiskEngineWeight(parseFloat(e.target.value))}
                className="w-full accent-[var(--color-accent)]"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1 text-[var(--color-text-secondary)]">
                <span>Citizen Complaint Weight: {complaintWeight}</span>
                <span className="text-[var(--color-text-muted)]">Public grievances & escalations</span>
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
              <div className="flex justify-between mb-1 text-[var(--color-text-secondary)]">
                <span>E-Commerce Flag Weight: {ecommerceWeight}</span>
                <span className="text-[var(--color-text-muted)]">Digital catalog discrepancies</span>
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
              <span className="text-[11px] text-[var(--color-text-muted)]">
                Repeat Offense Multiplier: <strong>{repeatMultiplier}x</strong>
              </span>
              <button
                type="submit"
                disabled={updateWeightsMutation.isPending}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-[var(--color-text-primary)] cursor-pointer disabled:opacity-50"
                style={{ background: 'var(--color-accent)' }}
              >
                {updateWeightsMutation.isPending ? 'Saving...' : 'Save priority weights'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
