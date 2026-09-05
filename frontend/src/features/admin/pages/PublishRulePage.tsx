/**
 * Publish Rule Page (Step G).
 * Route: /admin/rules/:id/publish
 * Sets effective date, archives superseded versions, and activates rule live.
 */
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../api';
import type { RuleItem } from '../types';

export default function PublishRulePage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [effectiveDate, setEffectiveDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [publishedRule, setPublishedRule] = useState<RuleItem | null>(null);
  const [errorMessage, setErrorMessage] = useState('');

  const { data: draft, isLoading, error } = useQuery({
    queryKey: ['admin-draft', id],
    queryFn: () => adminApi.getDraft(id!),
    enabled: !!id,
  });

  const publishMutation = useMutation({
    mutationFn: () => adminApi.publishDraft(id!, { effective_date: effectiveDate }),
    onSuccess: (liveRule) => {
      setPublishedRule(liveRule);
      setShowConfirmModal(false);
      queryClient.invalidateQueries({ queryKey: ['admin-draft', id] });
      queryClient.invalidateQueries({ queryKey: ['admin-notifications'] });
    },
    onError: (err: any) => {
      setErrorMessage(err?.response?.data?.error || 'Failed to publish rule.');
      setShowConfirmModal(false);
    },
  });

  if (isLoading) {
    return (
      <div className="glass-card p-12 text-center text-[var(--color-text-muted)] animate-pulse">
        Loading draft publication data...
      </div>
    );
  }

  if (error || !draft) {
    return (
      <div className="glass-card p-8 text-center text-red-400">
        Failed to load draft #{id} for publication.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-card p-6 border-l-4 border-green-300 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-green-200">
              Rule Publication &middot; Step G
            </span>
            <span className="text-xs text-[var(--color-text-muted)] font-mono">Live Activation</span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mt-1">Publish Rule to Repository</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-0.5">
            Activate versioned rule into the National Legal Metrology Compliance Engine.
          </p>
        </div>

        <button
          onClick={() => navigate('/admin/rules')}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--color-surface-tertiary)] hover:bg-gray-100 text-[var(--color-text-primary)] border border-[var(--color-border)] cursor-pointer"
        >
          View Rule Repository &rarr;
        </button>
      </div>

      {/* Success View */}
      {publishedRule ? (
        <div className="glass-card p-8 border border-green-200 bg-green-50 space-y-6 text-center animate-fade-in">
          <div className="w-16 h-16 rounded-full bg-[var(--color-accent)]/20 text-[var(--color-accent)] text-3xl flex items-center justify-center mx-auto border border-green-200">
            ✓
          </div>

          <div className="space-y-1">
            <h2 className="text-xl font-bold text-[var(--color-text-primary)]">Rule Successfully Published & Activated Live</h2>
            <p className="text-xs text-[var(--color-text-secondary)] font-mono">
              Rule ID: <strong>{publishedRule.rule_id_code}</strong> &middot; Effective From:{' '}
              <strong>{publishedRule.effective_from}</strong>
            </p>
          </div>

          <div className="max-w-xl mx-auto p-4 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-left text-xs space-y-2">
            <div className="flex justify-between">
              <span className="text-[var(--color-text-muted)]">Section Ref:</span>
              <span className="text-[var(--color-text-primary)] font-medium">{publishedRule.section_ref}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-text-muted)]">Category:</span>
              <span className="text-[var(--color-accent)] font-semibold uppercase">{publishedRule.category}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-text-muted)]">Status:</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[var(--color-accent)]/20 text-[var(--color-accent)]">
                IN_FORCE
              </span>
            </div>
            {draft.supersedes_rule_code && (
              <div className="flex justify-between text-amber-600">
                <span>Superseded Prior Rule:</span>
                <span className="font-mono">{draft.supersedes_rule_code} (Archived)</span>
              </div>
            )}
          </div>

          <div className="flex justify-center gap-4">
            <button
              onClick={() => navigate('/admin/rules')}
              className="px-6 py-2.5 rounded-xl text-xs font-semibold bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-[var(--color-text-primary)] shadow-lg cursor-pointer"
            >
              Explore Live Repository
            </button>
            <button
              onClick={() => navigate('/admin/rules/notifications')}
              className="px-5 py-2.5 rounded-xl text-xs font-medium bg-[var(--color-surface-tertiary)] hover:bg-gray-100 text-[var(--color-text-secondary)] cursor-pointer"
            >
              Review Another Notification
            </button>
          </div>
        </div>
      ) : (
        /* Pre-Publication Form */
        <div className="glass-card p-6 border border-[var(--color-border)] space-y-6">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-950/40 border border-red-700 text-xs text-red-300">
              ⚠ {errorMessage}
            </div>
          )}

          {/* Details Table */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-[var(--color-text-primary)] uppercase tracking-wider">
              Publication Summary & Verification
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] space-y-2 text-xs">
                <div className="text-[var(--color-text-muted)]">Rule Code:</div>
                <div className="text-base font-bold text-[var(--color-text-primary)] font-mono">{draft.rule_id_code}</div>

                <div className="text-[var(--color-text-muted)] pt-2">Section Reference:</div>
                <div className="text-[var(--color-text-primary)]">{draft.section_ref}</div>

                <div className="text-[var(--color-text-muted)] pt-2">Applicability:</div>
                <div className="text-[var(--color-accent)] font-semibold uppercase">{draft.category}</div>
              </div>

              <div className="p-4 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] space-y-3 text-xs">
                <label className="block text-[var(--color-text-secondary)] font-medium">Effective Date on Live System *</label>
                <input
                  type="date"
                  value={effectiveDate}
                  onChange={(e) => setEffectiveDate(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)]"
                  style={{ backgroundColor: 'var(--color-surface-tertiary)', color: 'var(--color-text-primary)' }}
                />
                <p className="text-[11px] text-[var(--color-text-muted)]">
                  Inspections conducted on or after this date will evaluate against this rule condition.
                </p>

                {draft.supersedes_rule_code && (
                  <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-800/40 text-[11px] text-amber-600">
                    ℹ Will supersede active rule: <strong>{draft.supersedes_rule_code}</strong>.
                  </div>
                )}
              </div>
            </div>

            {/* Condition Schema Preview */}
            <div className="p-4 rounded-xl bg-[var(--color-surface-primary)]/80 border border-[var(--color-border)] space-y-2">
              <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase">
                Active Condition Configuration
              </span>
              <pre className="text-xs text-[var(--color-accent)] font-mono overflow-x-auto">
                {JSON.stringify(draft.proposed_condition, null, 2)}
              </pre>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={() => navigate(`/admin/rules/${draft.id}/review`)}
              className="px-4 py-2 rounded-xl text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] cursor-pointer"
            >
              &larr; Back to Review
            </button>
            <button
              onClick={() => setShowConfirmModal(true)}
              className="px-6 py-2.5 rounded-xl text-xs font-semibold bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-[var(--color-text-primary)] shadow-lg cursor-pointer"
            >
              🚀 Finalize & Publish Live
            </button>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[var(--color-surface-tertiary)]/80 backdrop-blur-sm animate-fade-in">
          <div className="glass-card max-w-md w-full p-6 space-y-4 border border-emerald-600/40">
            <h3 className="text-lg font-bold text-[var(--color-text-primary)]">Confirm Rule Publication</h3>
            <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
              Are you sure you want to publish <strong className="text-[var(--color-accent)]">{draft.rule_id_code}</strong> into the live rule repository effective <strong>{effectiveDate}</strong>?
            </p>
            <p className="text-xs text-[var(--color-text-muted)]">
              This action writes to the live legal repository and generates an audit log entry.
            </p>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="px-4 py-2 rounded-xl text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => publishMutation.mutate()}
                disabled={publishMutation.isPending}
                className="px-5 py-2 rounded-xl text-xs font-semibold bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-[var(--color-text-primary)] cursor-pointer disabled:opacity-50"
              >
                {publishMutation.isPending ? 'Publishing...' : 'Yes, Publish Live'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
