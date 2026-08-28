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
      <div className="glass-card p-12 text-center text-slate-400 animate-pulse">
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
      <div className="glass-card p-6 border-l-4 border-emerald-500 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              Rule Publication &middot; Step G
            </span>
            <span className="text-xs text-slate-400 font-mono">Live Activation</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">Publish Rule to Repository</h1>
          <p className="text-sm text-slate-300 mt-0.5">
            Activate versioned rule into the National Legal Metrology Compliance Engine.
          </p>
        </div>

        <button
          onClick={() => navigate('/admin/rules')}
          className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 cursor-pointer"
        >
          View Rule Repository &rarr;
        </button>
      </div>

      {/* Success View */}
      {publishedRule ? (
        <div className="glass-card p-8 border border-emerald-500/50 bg-emerald-950/20 space-y-6 text-center animate-fade-in">
          <div className="w-16 h-16 rounded-full bg-emerald-500/20 text-emerald-300 text-3xl flex items-center justify-center mx-auto border border-emerald-500/30">
            ✓
          </div>

          <div className="space-y-1">
            <h2 className="text-xl font-bold text-white">Rule Successfully Published & Activated Live</h2>
            <p className="text-xs text-slate-300 font-mono">
              Rule ID: <strong>{publishedRule.rule_id_code}</strong> &middot; Effective From:{' '}
              <strong>{publishedRule.effective_from}</strong>
            </p>
          </div>

          <div className="max-w-xl mx-auto p-4 rounded-xl bg-slate-900 border border-slate-800 text-left text-xs space-y-2">
            <div className="flex justify-between">
              <span className="text-slate-400">Section Ref:</span>
              <span className="text-white font-medium">{publishedRule.section_ref}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Category:</span>
              <span className="text-emerald-400 font-semibold uppercase">{publishedRule.category}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Status:</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300">
                IN_FORCE
              </span>
            </div>
            {draft.supersedes_rule_code && (
              <div className="flex justify-between text-amber-400">
                <span>Superseded Prior Rule:</span>
                <span className="font-mono">{draft.supersedes_rule_code} (Archived)</span>
              </div>
            )}
          </div>

          <div className="flex justify-center gap-4">
            <button
              onClick={() => navigate('/admin/rules')}
              className="px-6 py-2.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg cursor-pointer"
            >
              Explore Live Repository
            </button>
            <button
              onClick={() => navigate('/admin/rules/notifications')}
              className="px-5 py-2.5 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 cursor-pointer"
            >
              Review Another Notification
            </button>
          </div>
        </div>
      ) : (
        /* Pre-Publication Form */
        <div className="glass-card p-6 border border-slate-800 space-y-6">
          {errorMessage && (
            <div className="p-3 rounded-lg bg-red-950/40 border border-red-700 text-xs text-red-300">
              ⚠ {errorMessage}
            </div>
          )}

          {/* Details Table */}
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Publication Summary & Verification
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2 text-xs">
                <div className="text-slate-400">Rule Code:</div>
                <div className="text-base font-bold text-white font-mono">{draft.rule_id_code}</div>

                <div className="text-slate-400 pt-2">Section Reference:</div>
                <div className="text-slate-200">{draft.section_ref}</div>

                <div className="text-slate-400 pt-2">Applicability:</div>
                <div className="text-indigo-300 font-semibold uppercase">{draft.category}</div>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 text-xs">
                <label className="block text-slate-300 font-medium">Effective Date on Live System *</label>
                <input
                  type="date"
                  value={effectiveDate}
                  onChange={(e) => setEffectiveDate(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-white"
                />
                <p className="text-[11px] text-slate-400">
                  Inspections conducted on or after this date will evaluate against this rule condition.
                </p>

                {draft.supersedes_rule_code && (
                  <div className="p-2.5 rounded-lg bg-amber-950/30 border border-amber-800/40 text-[11px] text-amber-300">
                    ℹ Will supersede active rule: <strong>{draft.supersedes_rule_code}</strong>.
                  </div>
                )}
              </div>
            </div>

            {/* Condition Schema Preview */}
            <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
              <span className="text-xs font-semibold text-slate-400 uppercase">
                Active Condition Configuration
              </span>
              <pre className="text-xs text-emerald-400 font-mono overflow-x-auto">
                {JSON.stringify(draft.proposed_condition, null, 2)}
              </pre>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={() => navigate(`/admin/rules/${draft.id}/review`)}
              className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white cursor-pointer"
            >
              &larr; Back to Review
            </button>
            <button
              onClick={() => setShowConfirmModal(true)}
              className="px-6 py-2.5 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg cursor-pointer"
            >
              🚀 Finalize & Publish Live
            </button>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="glass-card max-w-md w-full p-6 space-y-4 border border-emerald-600/40">
            <h3 className="text-lg font-bold text-white">Confirm Rule Publication</h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Are you sure you want to publish <strong className="text-emerald-400">{draft.rule_id_code}</strong> into the live rule repository effective <strong>{effectiveDate}</strong>?
            </p>
            <p className="text-xs text-slate-400">
              This action writes to the live legal repository and generates an audit log entry.
            </p>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setShowConfirmModal(false)}
                className="px-4 py-2 rounded-xl text-xs text-slate-400 hover:text-white cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => publishMutation.mutate()}
                disabled={publishMutation.isPending}
                className="px-5 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer disabled:opacity-50"
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
