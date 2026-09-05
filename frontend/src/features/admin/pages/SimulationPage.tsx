/**
 * Sandbox Simulation Page (Steps H6–H7).
 * Route: /admin/rules/:id/simulate
 * Runs read-only simulation of draft rules against historical scan data.
 */
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../api';
import type { RuleSimulationResult } from '../types';

export default function SimulationPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [latestSimResult, setLatestSimResult] = useState<RuleSimulationResult | null>(null);

  const { data: draft, isLoading, error } = useQuery({
    queryKey: ['admin-draft', id],
    queryFn: () => adminApi.getDraft(id!),
    enabled: !!id,
  });

  const simulateMutation = useMutation({
    mutationFn: () => adminApi.simulateDraft(id!),
    onSuccess: (result) => {
      setLatestSimResult(result);
      queryClient.invalidateQueries({ queryKey: ['admin-draft', id] });
    },
  });

  const activeResult = latestSimResult || (draft?.simulation_results && draft.simulation_results[0]);

  if (isLoading) {
    return (
      <div className="glass-card p-12 text-center text-[var(--color-text-muted)] animate-pulse">
        Loading sandbox simulation environment...
      </div>
    );
  }

  if (error || !draft) {
    return (
      <div className="glass-card p-8 text-center text-red-400">
        Failed to load draft #{id} for simulation.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-card p-6 border-l-4 border-purple-500 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-purple-50 text-purple-300 border border-purple-200">
              Sandbox Simulation &middot; Steps H6–H7
            </span>
            <span className="text-xs text-[var(--color-text-muted)] font-mono">Draft #{draft.id}</span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mt-1">
            Impact Analysis: {draft.rule_id_code}
          </h1>
          <p className="text-xs text-[var(--color-text-secondary)] font-mono mt-0.5">{draft.section_ref}</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => simulateMutation.mutate()}
            disabled={simulateMutation.isPending}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-[var(--color-text-primary)] shadow-lg transition-all cursor-pointer disabled:opacity-50"
          >
            {simulateMutation.isPending ? 'Simulating Historical Data...' : '⚡ Run Simulation Now'}
          </button>
          <button
            onClick={() => navigate(`/admin/rules/${draft.id}/publish`)}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-[var(--color-text-primary)] shadow-md cursor-pointer"
          >
            Proceed to Publish &rarr;
          </button>
        </div>
      </div>

      {/* Draft Rule Condition Summary */}
      <div className="glass-card p-4 border border-[var(--color-border)] flex items-center justify-between text-xs">
        <div>
          <span className="text-[var(--color-text-muted)]">Evaluating Condition: </span>
          <span className="font-mono text-[var(--color-accent)] font-semibold">
            {draft.proposed_condition?.type || 'required_field'} ({draft.proposed_condition?.field || 'mfg_date'})
          </span>
        </div>
        <div className="text-[var(--color-text-muted)]">
          Target Category: <strong className="text-[var(--color-text-primary)] uppercase">{draft.category}</strong>
        </div>
      </div>

      {/* Simulation Results Display */}
      {activeResult ? (
        <div className="space-y-6 animate-fade-in">
          {/* Key Metrics Comparison Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Before Rate */}
            <div className="glass-card p-5 border border-[var(--color-border)] space-y-1">
              <span className="text-xs font-semibold uppercase text-[var(--color-text-muted)]">
                Baseline Compliance (Before)
              </span>
              <div className="text-3xl font-extrabold text-blue-600">
                {activeResult.before_compliance_rate.toFixed(1)}%
              </div>
              <p className="text-[11px] text-[var(--color-text-muted)]">Based on historical in-force rule evaluations</p>
            </div>

            {/* After Rate */}
            <div className="glass-card p-5 border border-[var(--color-border)] space-y-1">
              <span className="text-xs font-semibold uppercase text-[var(--color-text-muted)]">
                Projected Compliance (After)
              </span>
              <div
                className={`text-3xl font-extrabold ${
                  activeResult.after_compliance_rate >= activeResult.before_compliance_rate
                    ? 'text-[var(--color-accent)]'
                    : 'text-amber-600'
                }`}
              >
                {activeResult.after_compliance_rate.toFixed(1)}%
              </div>
              <p className="text-[11px] text-[var(--color-text-muted)]">
                Shift: {(activeResult.after_compliance_rate - activeResult.before_compliance_rate).toFixed(1)}%
              </p>
            </div>

            {/* Projected Violation Change */}
            <div className="glass-card p-5 border border-[var(--color-border)] space-y-1">
              <span className="text-xs font-semibold uppercase text-[var(--color-text-muted)]">
                Projected Violation Volume
              </span>
              <div className="text-3xl font-extrabold text-red-600">
                +{activeResult.projected_violation_diff} Cases
              </div>
              <p className="text-[11px] text-[var(--color-text-muted)]">
                Across {activeResult.total_scans_evaluated} evaluated inspections
              </p>
            </div>
          </div>

          {/* Impact Summary */}
          <div className="glass-card p-5 border border-purple-900/40 bg-purple-950/20 space-y-2">
            <h3 className="text-xs font-bold text-purple-300 uppercase tracking-wider">
              Simulation Intelligence Summary
            </h3>
            <p className="text-xs text-[var(--color-text-primary)] leading-relaxed font-sans">
              {activeResult.metrics?.impact_summary ||
                `Evaluated against ${activeResult.total_scans_evaluated} historical inspections. Compliance rate changes from ${activeResult.before_compliance_rate}% to ${activeResult.after_compliance_rate}%.`}
            </p>
          </div>

          {/* Category Breakdown & Affected Brands */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Category Breakdown */}
            <div className="glass-card p-5 border border-[var(--color-border)] space-y-3">
              <h4 className="text-xs font-bold text-[var(--color-text-secondary)] uppercase tracking-wider">
                Category Compliance Distribution
              </h4>
              <div className="space-y-3">
                {Object.entries(activeResult.metrics?.category_breakdown || {}).map(([cat, val]: any) => (
                  <div key={cat} className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="capitalize text-[var(--color-text-secondary)]">{cat}</span>
                      <span className="text-[var(--color-text-muted)] font-mono">
                        +{val.new_violations || 0} New Violations
                      </span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-[var(--color-surface-tertiary)] overflow-hidden flex">
                      <div
                        className="bg-[var(--color-accent)] h-full"
                        style={{ width: `${Math.min(100, (val.after_compliant / (val.before_compliant + 1)) * 100)}%` }}
                      />
                      <div
                        className="bg-rose-500 h-full"
                        style={{ width: `${Math.min(100, (val.new_violations / (val.before_compliant + 1)) * 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Affected Brands Sample */}
            <div className="glass-card p-5 border border-[var(--color-border)] space-y-3">
              <h4 className="text-xs font-bold text-[var(--color-text-secondary)] uppercase tracking-wider">
                Sample Impacted Brands
              </h4>
              <p className="text-xs text-[var(--color-text-muted)]">
                Brands that would require labeling adjustment under the new thresholds:
              </p>
              <div className="flex flex-wrap gap-2 pt-1">
                {(activeResult.metrics?.affected_brands_sample || ['PureFoods', 'DailyDelight', 'Mediterra']).map((brand: string) => (
                  <span
                    key={brand}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)] border border-[var(--color-border)]"
                  >
                    🏷 {brand}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Empty State */
        <div className="glass-card p-12 text-center space-y-4">
          <div className="text-4xl">📊</div>
          <h3 className="text-base font-bold text-[var(--color-text-primary)]">No Simulation Run Yet</h3>
          <p className="text-xs text-[var(--color-text-muted)] max-w-md mx-auto">
            Click "Run Simulation Now" to test this proposed rule draft against stored historical scans without altering any live data.
          </p>
          <button
            onClick={() => simulateMutation.mutate()}
            disabled={simulateMutation.isPending}
            className="px-6 py-2.5 rounded-xl text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-[var(--color-text-primary)] cursor-pointer"
          >
            {simulateMutation.isPending ? 'Simulating...' : '⚡ Run Simulation Now'}
          </button>
        </div>
      )}
    </div>
  );
}
