/**
 * Rule Repository Page.
 * Route: /admin/rules
 * Filterable and searchable repository of all legal metrology rules.
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { adminApi } from '../api';
import type { RuleItem } from '../types';

export default function RuleRepositoryPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [selectedRule, setSelectedRule] = useState<RuleItem | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-rules-repository', statusFilter, categoryFilter, searchTerm],
    queryFn: () =>
      adminApi.getRules({
        status: statusFilter !== 'all' ? statusFilter : undefined,
        category: categoryFilter !== 'all' ? categoryFilter : undefined,
        search: searchTerm.trim() || undefined,
      }),
  });

  const rules = data?.results || [];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="glass-card p-6 border-l-4 border-indigo-500 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-[var(--color-accent)]">
              National Repository
            </span>
            <span className="text-xs text-[var(--color-text-muted)]">Rule Engine Version Registry</span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mt-1">Live Legal Metrology Rules Repository</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-0.5">
            Full registry of packaged commodity regulations, condition schemas, and version lineage.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/admin/rules/notifications')}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-[var(--color-accent)] hover:bg-[var(--color-accent-hover)] text-[var(--color-text-primary)] shadow-md transition-all cursor-pointer"
          >
            🔔 Review Incoming Notifications &rarr;
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="glass-card p-4 space-y-3 border border-[var(--color-border)]">
        <div className="flex flex-col md:flex-row items-center gap-3">
          {/* Search */}
          <div className="w-full md:flex-1">
            <input
              type="text"
              placeholder="Search by rule code, section reference, or keyword..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] outline-none"
              style={{ backgroundColor: 'var(--color-surface-tertiary)', color: 'var(--color-text-primary)' }}
            />
          </div>

          {/* Category Filter */}
          <div className="w-full md:w-auto">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full md:w-auto px-3 py-2 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)] outline-none"
              style={{ backgroundColor: 'var(--color-surface-tertiary)', color: 'var(--color-text-primary)' }}
            >
              <option value="all" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">All Categories</option>
              <option value="general" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">General</option>
              <option value="food" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Food & Beverages</option>
              <option value="electronics" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Electronics</option>
              <option value="medical_device" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Medical Devices</option>
              <option value="import" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Imported Goods</option>
              <option value="ecommerce" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">E-Commerce</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="w-full md:w-auto flex items-center gap-1 bg-[var(--color-surface-tertiary)] p-1 rounded-xl border border-[var(--color-border)]">
            {['all', 'in_force', 'draft', 'repealed'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all cursor-pointer ${
                  statusFilter === st
                    ? 'bg-[var(--color-accent)] text-[var(--color-text-primary)] shadow'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
                }`}
              >
                {st.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Rules Table */}
      {isLoading ? (
        <div className="glass-card p-12 text-center text-[var(--color-text-muted)] animate-pulse">
          Loading rules repository...
        </div>
      ) : error ? (
        <div className="glass-card p-6 text-red-400">
          Failed to load rules repository.
        </div>
      ) : rules.length === 0 ? (
        <div className="glass-card p-12 text-center text-[var(--color-text-muted)]">
          No rules matched the selected filter criteria.
        </div>
      ) : (
        <div className="glass-card overflow-hidden border border-[var(--color-border)]">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-muted)] uppercase tracking-wider text-[11px] border-b border-[var(--color-border)]">
                <tr>
                  <th className="px-4 py-3">Rule ID Code</th>
                  <th className="px-4 py-3">Section Reference</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Effective Range</th>
                  <th className="px-4 py-3">Condition Schema</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)]/60">
                {rules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-[var(--color-surface-tertiary)] transition-colors">
                    <td className="px-4 py-3.5 font-mono font-bold text-[var(--color-accent)]">
                      {rule.rule_id_code}
                      {rule.superseded_by_code && (
                        <div className="text-[10px] text-amber-600 font-sans font-normal mt-0.5">
                          Superseded by: {rule.superseded_by_code}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-[var(--color-text-primary)] max-w-xs">{rule.section_ref}</td>
                    <td className="px-4 py-3.5">
                      <span className="px-2 py-0.5 rounded bg-[var(--color-surface-tertiary)] text-[var(--color-text-secondary)] uppercase font-semibold text-[10px]">
                        {rule.category}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-[var(--color-text-muted)] font-mono text-[11px]">
                      {rule.effective_from} {rule.effective_to ? `to ${rule.effective_to}` : 'to present'}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-[var(--color-accent)] text-[11px]">
                      {rule.condition?.type || 'required_field'}
                      {rule.condition?.field ? ` (${rule.condition.field})` : ''}
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          rule.status === 'in_force'
                            ? 'bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-green-200'
                            : rule.status === 'draft'
                            ? 'bg-amber-50 text-amber-600 border border-amber-200'
                            : 'bg-red-50 text-red-600 border border-red-200'
                        }`}
                      >
                        {rule.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <button
                        onClick={() => setSelectedRule(rule)}
                        className="px-2.5 py-1 rounded bg-[var(--color-surface-tertiary)] hover:bg-gray-100 text-[var(--color-text-secondary)] text-[11px] cursor-pointer"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Rule Inspect Modal */}
      {selectedRule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[var(--color-surface-tertiary)]/80 backdrop-blur-sm animate-fade-in">
          <div className="glass-card max-w-xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto border border-[var(--color-border)]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-[var(--color-accent)] font-bold">
                {selectedRule.rule_id_code}
              </span>
              <button
                onClick={() => setSelectedRule(null)}
                className="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] text-lg font-bold cursor-pointer"
              >
                &times;
              </button>
            </div>

            <h3 className="text-base font-bold text-[var(--color-text-primary)]">{selectedRule.section_ref}</h3>

            <div className="grid grid-cols-2 gap-3 text-xs p-3 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)]">
              <div>
                <span className="text-[var(--color-text-muted)]">Category:</span>
                <p className="text-[var(--color-text-primary)] font-medium uppercase">{selectedRule.category}</p>
              </div>
              <div>
                <span className="text-[var(--color-text-muted)]">Status:</span>
                <p className="text-[var(--color-accent)] font-bold uppercase">{selectedRule.status}</p>
              </div>
              <div>
                <span className="text-[var(--color-text-muted)]">Effective From:</span>
                <p className="text-[var(--color-text-secondary)] font-mono">{selectedRule.effective_from}</p>
              </div>
              <div>
                <span className="text-[var(--color-text-muted)]">Effective To:</span>
                <p className="text-[var(--color-text-secondary)] font-mono">{selectedRule.effective_to || 'In Force'}</p>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-[var(--color-text-muted)] mb-1">
                Condition Engine Schema (JSON)
              </label>
              <pre className="p-3 rounded-xl bg-[var(--color-surface-primary)] border border-[var(--color-border)] text-xs text-[var(--color-accent)] font-mono overflow-x-auto">
                {JSON.stringify(selectedRule.condition, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedRule(null)}
                className="px-4 py-2 rounded-xl text-xs font-medium bg-[var(--color-surface-tertiary)] text-[var(--color-text-secondary)] hover:bg-gray-100 cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
