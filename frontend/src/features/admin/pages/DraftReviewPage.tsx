/**
 * Draft Review Page (Steps C, D, E, F).
 * Route: /admin/rules/:id/review
 * Displays side-by-side legal clause diff with in-place Revise and Approve workflows.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../api';

export default function DraftReviewPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [newClauseText, setNewClauseText] = useState('');
  const [oldClauseText, setOldClauseText] = useState('');
  const [conditionJsonStr, setConditionJsonStr] = useState('');
  const [category, setCategory] = useState('general');
  const [effectiveDate, setEffectiveDate] = useState('');
  const [comment, setComment] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const { data: draft, isLoading, error } = useQuery({
    queryKey: ['admin-draft', id],
    queryFn: () => adminApi.getDraft(id!),
    enabled: !!id,
  });

  useEffect(() => {
    if (draft) {
      const timer = setTimeout(() => {
        setNewClauseText(draft.new_clause_text || '');
        setOldClauseText(draft.old_clause_text || '');
        setConditionJsonStr(JSON.stringify(draft.proposed_condition || {}, null, 2));
        setCategory(draft.category || 'general');
        setEffectiveDate(draft.effective_date || new Date().toISOString().split('T')[0]);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [draft]);

  // Revise Mutation
  const reviseMutation = useMutation({
    mutationFn: (payload: any) => adminApi.reviseDraft(id!, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['admin-draft', id], updated);
      queryClient.invalidateQueries({ queryKey: ['admin-draft', id] });
      setIsEditing(false);
      setComment('');
      setSuccessMessage('Draft successfully revised in place without duplicating records.');
      setTimeout(() => setSuccessMessage(''), 4000);
    },
    onError: (err: any) => {
      setErrorMessage(err?.response?.data?.error || 'Failed to update revision.');
    },
  });

  // Approve Mutation
  const approveMutation = useMutation({
    mutationFn: (payload: { effective_date: string; comment?: string }) =>
      adminApi.approveDraft(id!, payload),
    onSuccess: (updated) => {
      queryClient.setQueryData(['admin-draft', id], updated);
      queryClient.invalidateQueries({ queryKey: ['admin-draft', id] });
      setSuccessMessage('Draft approved! Ready for simulation and live publication.');
      setTimeout(() => setSuccessMessage(''), 4000);
    },
    onError: (err: any) => {
      setErrorMessage(err?.response?.data?.error || 'Failed to approve draft.');
    },
  });

  const handleReviseSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage('');
    let parsedCondition = {};
    try {
      parsedCondition = JSON.parse(conditionJsonStr);
    } catch {
      setErrorMessage('Condition must be valid JSON format.');
      return;
    }

    reviseMutation.mutate({
      new_clause_text: newClauseText,
      old_clause_text: oldClauseText,
      proposed_condition: parsedCondition,
      category,
      comment: comment.trim() || 'Admin revised draft clauses and condition parameters.',
    });
  };

  const handleApproveSubmit = () => {
    setErrorMessage('');
    if (!effectiveDate) {
      setErrorMessage('Please select a valid planned effective date.');
      return;
    }
    approveMutation.mutate({
      effective_date: effectiveDate,
      comment: comment.trim() || 'Draft approved by National Admin.',
    });
  };

  if (isLoading) {
    return (
      <div className="glass-card p-12 text-center text-[var(--color-text-muted)] animate-pulse">
        Loading rule draft review data...
      </div>
    );
  }

  if (error || !draft) {
    return (
      <div className="glass-card p-8 text-center space-y-4">
        <p className="text-red-400">Failed to load rule draft #{id}.</p>
        <button
          onClick={() => navigate('/admin/rules/notifications')}
          className="px-4 py-2 rounded-xl text-xs bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]"
        >
          &larr; Back to Notifications
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-card p-6 border-l-4 border-indigo-500 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-[var(--color-accent)]">
              Admin Review &middot; Steps C & D
            </span>
            <span
              className={`text-xs px-2 py-0.5 rounded font-semibold ${
                draft.status === 'approved'
                  ? 'bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-green-200'
                  : draft.status === 'revised'
                  ? 'bg-amber-50 text-amber-600 border border-amber-200'
                  : draft.status === 'published'
                  ? 'bg-blue-50 text-blue-600 border border-blue-200'
                  : 'bg-gray-100 text-[var(--color-text-secondary)]'
              }`}
            >
              Status: {draft.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mt-1">{draft.rule_id_code}</h1>
          <p className="text-xs text-[var(--color-text-secondary)] font-mono mt-0.5">{draft.section_ref}</p>
        </div>

        {/* Quick Action Navigation */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => navigate(`/admin/rules/${draft.id}/simulate`)}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-purple-900/60 hover:bg-purple-800 text-purple-200 border border-purple-700 transition-all cursor-pointer"
          >
            📊 Run Sandbox Simulation
          </button>
          <button
            onClick={() => navigate(`/admin/rules/${draft.id}/publish`)}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-white shadow-sm transition-all cursor-pointer"
          >
            🚀 Publish Rule Live
          </button>
        </div>
      </div>

      {/* Messages */}
      {successMessage && (
        <div className="glass-card p-4 bg-green-50 border border-green-200 text-xs text-[var(--color-accent)]">
          ✓ {successMessage}
        </div>
      )}
      {errorMessage && (
        <div className="glass-card p-4 bg-red-950/40 border border-red-700 text-xs text-red-300">
          ⚠ {errorMessage}
        </div>
      )}

      {/* Main Diff Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Left: Old Clause (In Force) */}
        <div className="glass-card p-5 border border-rose-900/40 space-y-3 bg-[var(--color-surface-primary)]/40">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-red-600 uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-rose-500"></span> Old Clause (In-Force)
            </span>
            {draft.supersedes_rule_code && (
              <span className="text-xs text-[var(--color-text-muted)] font-mono">
                Replaces: {draft.supersedes_rule_code}
              </span>
            )}
          </div>

          {isEditing ? (
            <textarea
              rows={4}
              value={oldClauseText}
              onChange={(e) => setOldClauseText(e.target.value)}
              className="w-full p-3 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)] font-mono"
            />
          ) : (
            <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-900/30 text-xs text-[var(--color-text-secondary)] font-serif leading-relaxed min-h-[100px]">
              {draft.old_clause_text || 'No previous specific clause (new regulation addition).'}
            </div>
          )}
        </div>

        {/* Right: New Clause (Proposed Amendment) */}
        <div className="glass-card p-5 border border-emerald-900/40 space-y-3 bg-[var(--color-surface-primary)]/40">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-[var(--color-accent)] uppercase tracking-wider flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[var(--color-accent)]"></span> Proposed New Clause
            </span>
            <span className="text-xs text-[var(--color-text-muted)]">Category: {draft.category}</span>
          </div>

          {isEditing ? (
            <textarea
              rows={4}
              value={newClauseText}
              onChange={(e) => setNewClauseText(e.target.value)}
              className="w-full p-3 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)] font-mono"
            />
          ) : (
            <div className="p-4 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)] font-serif leading-relaxed min-h-[100px]">
              {draft.new_clause_text}
            </div>
          )}
        </div>
      </div>

      {/* Proposed Condition Schema Card */}
      <div className="glass-card p-5 space-y-3 border border-[var(--color-border)]">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--color-accent)]">
            Engine Condition Schema (JSONB)
          </h3>
          <span className="text-xs text-[var(--color-text-muted)] font-mono">
            Type: {draft.proposed_condition?.type || 'required_field'}
          </span>
        </div>

        {isEditing ? (
          <textarea
            rows={5}
            value={conditionJsonStr}
            onChange={(e) => setConditionJsonStr(e.target.value)}
            className="w-full p-3 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-accent)] font-mono"
          />
        ) : (
          <pre className="p-4 rounded-xl bg-[var(--color-surface-primary)]/80 border border-[var(--color-border)] text-xs text-[var(--color-accent)] font-mono overflow-x-auto">
            {JSON.stringify(draft.proposed_condition, null, 2)}
          </pre>
        )}
      </div>

      {/* Decision Section: Revise (E) vs Approve (F) */}
      <div className="glass-card p-6 border border-[var(--color-border)] space-y-4">
        <h3 className="text-sm font-bold text-[var(--color-text-primary)] uppercase tracking-wider">
          Admin Decision Workflow &middot; Step D
        </h3>

        {!isEditing ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Approve form */}
              <div className="p-4 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] space-y-3">
                <h4 className="text-xs font-bold text-[var(--color-accent)] uppercase">
                  Approve Draft (Yes Branch &middot; Step F)
                </h4>
                <div>
                  <label className="block text-xs text-[var(--color-text-muted)] mb-1">Effective Date *</label>
                  <input
                    type="date"
                    value={effectiveDate}
                    onChange={(e) => setEffectiveDate(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)]"
                  />
                </div>
                <div>
                  <label className="block text-xs text-[var(--color-text-muted)] mb-1">Approval Comment</label>
                  <input
                    type="text"
                    placeholder="e.g. Approved after legal metrology review."
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)]"
                  />
                </div>
                <button
                  onClick={handleApproveSubmit}
                  disabled={approveMutation.isPending}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-[var(--color-text-primary)] cursor-pointer disabled:opacity-50"
                >
                  {approveMutation.isPending ? 'Approving...' : '✓ Approve Draft'}
                </button>
              </div>

              {/* Revise option */}
              <div className="p-4 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] space-y-3 flex flex-col justify-between">
                <div>
                  <h4 className="text-xs font-bold text-amber-600 uppercase">
                    Revise Draft (No Branch &middot; Step E)
                  </h4>
                  <p className="text-xs text-[var(--color-text-muted)] mt-1 leading-relaxed">
                    Edit the proposed legal clause, condition thresholds, or category scope in-place.
                    No duplicate rows will be created.
                  </p>
                </div>
                <button
                  onClick={() => setIsEditing(true)}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-[var(--color-surface-tertiary)] hover:bg-gray-100 text-amber-600 border border-amber-600/40 cursor-pointer"
                >
                  ✎ Edit & Revise Draft Clauses
                </button>
              </div>
            </div>
          </div>
        ) : (
          /* Inline Revise Form */
          <form onSubmit={handleReviseSubmit} className="space-y-4 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-[var(--color-text-muted)] mb-1">Target Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)]"
                >
                  <option value="general">General</option>
                  <option value="food">Food & Beverages</option>
                  <option value="electronics">Electronics</option>
                  <option value="medical_device">Medical Devices</option>
                  <option value="import">Imported Goods</option>
                  <option value="ecommerce">E-Commerce</option>
                </select>
              </div>
              <div>
                <label className="block text-xs text-[var(--color-text-muted)] mb-1">Revision Comment / Justification *</label>
                <input
                  type="text"
                  placeholder="Explain legal rationale for revision..."
                  required
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)]"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setIsEditing(false)}
                className="px-4 py-2 rounded-xl text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={reviseMutation.isPending}
                className="px-5 py-2 rounded-xl text-xs font-semibold bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-text-primary)] cursor-pointer disabled:opacity-50"
              >
                {reviseMutation.isPending ? 'Saving Revision...' : 'Save In-Place Revision'}
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Revision & Audit History Log */}
      {draft.comments && draft.comments.length > 0 && (
        <div className="glass-card p-5 border border-[var(--color-border)] space-y-3">
          <h4 className="text-xs font-bold text-[var(--color-text-secondary)] uppercase tracking-wider">
            Revision & Audit History
          </h4>
          <div className="space-y-2">
            {draft.comments.map((entry, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-[var(--color-text-primary)]">@{entry.admin}</span>
                    <span className="px-1.5 py-0.2 rounded text-[10px] uppercase font-mono bg-[var(--color-surface-tertiary)] text-[var(--color-accent)]">
                      {entry.action}
                    </span>
                  </div>
                  <p className="text-[var(--color-text-secondary)] mt-1">{entry.comment}</p>
                </div>
                <span className="text-[10px] text-[var(--color-text-muted)] font-mono">
                  {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
