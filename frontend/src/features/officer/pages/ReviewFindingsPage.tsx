import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../../services/apiClient';
import {
  confirmComplianceFinding,
  overrideComplianceFinding,
  type ComplianceCheckResult,
} from '../api';
import StatusPill from '../../../components/ui/StatusPill';
import RuleFindingCard from '../components/RuleFindingCard';
import ReportDownloadButton from '../components/ReportDownloadButton';

export default function ReviewFindingsPage() {
  const { checkId } = useParams<{ checkId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [notes, setNotes] = useState('');
  const [overrideVerdict, setOverrideVerdict] = useState<string>('compliant');
  const [showOverrideForm, setShowOverrideForm] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const { data: check, isLoading, error } = useQuery<ComplianceCheckResult>({
    queryKey: ['compliance-check-detail', checkId],
    queryFn: async () => {
      const { data } = await apiClient.get<ComplianceCheckResult>(`/compliance-checks/${checkId}/`);
      return data;
    },
    enabled: Boolean(checkId),
  });

  const confirmMutation = useMutation({
    mutationFn: () => confirmComplianceFinding(checkId || '0'),
    onSuccess: (data) => {
      setSuccessMessage(data.message);
      queryClient.invalidateQueries({ queryKey: ['compliance-check-detail', checkId] });
    },
  });

  const overrideMutation = useMutation({
    mutationFn: () =>
      overrideComplianceFinding(checkId || '0', {
        verdict: overrideVerdict,
        notes,
      }),
    onSuccess: (data) => {
      setSuccessMessage(data.message);
      setShowOverrideForm(false);
      queryClient.invalidateQueries({ queryKey: ['compliance-check-detail', checkId] });
    },
  });

  if (isLoading) {
    return (
      <div className="p-16 text-center text-muted-foreground glass-card rounded-2xl border border-border/50">
        <div className="animate-spin text-3xl mb-3">⚙️</div>
        <p>Loading compliance check review details...</p>
      </div>
    );
  }

  if (error || !check) {
    return (
      <div className="p-8 glass-card rounded-2xl border border-red-200 text-red-600 space-y-3">
        <h2 className="text-lg font-bold">Failed to load compliance check.</h2>
        <button onClick={() => navigate('/officer/queue')} className="px-4 py-2 bg-card border rounded-lg text-xs">
          ← Return to Queue
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200 text-xs font-semibold">
              Officer Review Panel
            </span>
            <span className="text-xs text-muted-foreground">Compliance Check #{check.id}</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground mt-1">Review & Sign-off Findings</h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(`/officer/product/${check.product_id}/history`)}
            className="px-3.5 py-2 rounded-lg bg-card/60 border border-border text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            Check History
          </button>
          {check.case_id ? (
            <button
              onClick={() => navigate(`/officer/case/${check.case_id}`)}
              className="px-4 py-2 rounded-lg bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-text-primary)] font-semibold text-xs transition-all flex items-center gap-1.5 shadow-md"
            >
              <span>View Generated Case</span>
              <span>→</span>
            </button>
          ) : (
            <button
              onClick={() =>
                navigate('/officer/case/new', {
                  state: {
                    productId: check.product_id,
                    productName: check.product_name,
                    brandName: check.brand_name,
                    violations: check.violations,
                  },
                })
              }
              className="px-4 py-2 rounded-lg bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-text-primary)] font-semibold text-xs transition-all flex items-center gap-1.5 shadow-md"
            >
              <span>Proceed to Case Creation</span>
              <span>→</span>
            </button>
          )}
        </div>
      </div>

      {/* Inspection PDF Report Generation Banner */}
      {checkId && (
        <ReportDownloadButton complianceCheckId={checkId} />
      )}

      {/* Success Notification */}
      {successMessage && (
        <div className="p-4 rounded-xl bg-[var(--color-accent)]/10 border border-green-200 text-[var(--color-accent)] text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>✓</span>
            <span>{successMessage}</span>
          </div>
          <button onClick={() => setSuccessMessage(null)} className="text-xs opacity-70 hover:opacity-100">✕</button>
        </div>
      )}

      {/* Summary Card */}
      <div className="p-6 rounded-2xl glass-card border border-border/70 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <span className="text-xs text-muted-foreground font-semibold">TARGET PRODUCT</span>
            <h2 className="text-xl font-bold text-foreground mt-0.5">
              {check.brand_name} — {check.product_name}
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <StatusPill verdict={check.verdict} />
            {check.reviewed_by_officer ? (
              <span className="px-3 py-1 rounded bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-green-200 text-xs font-semibold">
                ✓ Signed off by {check.reviewed_by_officer_username}
              </span>
            ) : (
              <span className="px-3 py-1 rounded bg-amber-50 text-amber-600 border border-amber-200 text-xs font-semibold">
                Awaiting Sign-off
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Findings Checklist */}
      <div className="space-y-3">
        <h3 className="text-sm font-bold text-foreground">Detected Findings & Rule Citations</h3>

        {check.report_data && (check.report_data.violations?.length > 0 || check.report_data.reviews?.length > 0) ? (
          <div className="space-y-3">
            {check.report_data.violations?.map((v) => (
              <RuleFindingCard key={v.rule_id} finding={v} defaultExpanded={true} />
            ))}
            {check.report_data.reviews?.map((r) => (
              <RuleFindingCard key={r.rule_id} finding={r} defaultExpanded={true} />
            ))}
          </div>
        ) : check.violations.length === 0 ? (
          <div className="p-6 rounded-xl glass-card border border-border/50 text-center text-xs text-muted-foreground">
            No violations recorded for this inspection scan.
          </div>
        ) : (
          check.violations.map((v) => (
            <div
              key={v.id}
              className="p-4 rounded-xl glass-card border border-border/60 space-y-2 flex flex-col md:flex-row md:items-start justify-between gap-4"
            >
              <div className="space-y-1 flex-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-red-50 text-red-600 border border-red-200 font-mono text-xs font-bold">
                    {v.rule_id_code}
                  </span>
                  <span className="text-xs text-muted-foreground">{v.section_ref}</span>
                </div>
                <p className="text-xs text-foreground/90 font-medium">{v.description}</p>
              </div>

              <span
                className={`px-2 py-1 rounded text-xs font-semibold self-start ${
                  v.is_first_time
                    ? 'bg-blue-50 text-blue-600 border border-blue-200'
                    : 'bg-red-50 text-red-600 border border-red-200'
                }`}
              >
                {v.is_first_time ? '1st-Time Procedural' : 'Repeat Offense'}
              </span>
            </div>
          ))
        )}
      </div>

      {/* Action Controls: Confirm vs Override */}
      <div className="p-6 rounded-2xl glass-card border border-border/70 space-y-4">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h4 className="text-sm font-bold text-foreground">Officer Verification Decision</h4>
            <p className="text-xs text-muted-foreground mt-0.5">
              Confirm automated AI engine evaluation or provide legal override with field justification.
            </p>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto">
            <button
              onClick={() => setShowOverrideForm(!showOverrideForm)}
              className="px-4 py-2 rounded-lg bg-card/70 border border-border text-xs font-semibold text-muted-foreground hover:text-foreground transition-all flex-1 sm:flex-none"
            >
              {showOverrideForm ? 'Cancel Override' : 'Override Verdict'}
            </button>

            <button
              onClick={() => confirmMutation.mutate()}
              disabled={confirmMutation.isPending}
              className="px-5 py-2 rounded-lg bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-[var(--color-text-primary)] font-semibold text-xs transition-all flex items-center justify-center gap-1.5 shadow-md flex-1 sm:flex-none"
            >
              <span>✓ Confirm & Sign-off</span>
            </button>
          </div>
        </div>

        {/* Override Form Panel */}
        {showOverrideForm && (
          <div className="p-4 rounded-xl bg-muted/30 border border-border space-y-3 pt-4 border-t border-border/50 animate-in fade-in">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-xs font-semibold text-foreground">New Override Verdict:</label>
                <select
                  value={overrideVerdict}
                  onChange={(e) => setOverrideVerdict(e.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-xs"
                  style={{ backgroundColor: 'var(--color-surface-tertiary)', color: 'var(--color-text-primary)' }}
                >
                  <option value="compliant" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Compliant (Exemption / Secondary Label Verified)</option>
                  <option value="non_compliant" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Non-Compliant (Confirmed Violation)</option>
                  <option value="needs_review" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Needs State Controller Review</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-foreground">Officer Justification / Notes:</label>
                <input
                  type="text"
                  placeholder="e.g., Exemption under Rule 26 verified during visual inspection..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="mt-1 w-full px-3 py-2 rounded bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] text-xs"
                  style={{ backgroundColor: 'var(--color-surface-tertiary)', color: 'var(--color-text-primary)' }}
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => overrideMutation.mutate()}
                disabled={overrideMutation.isPending}
                className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-[var(--color-text-primary)] font-semibold text-xs transition-all shadow-md"
              >
                Submit Legal Override
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
