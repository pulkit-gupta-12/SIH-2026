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
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
              National Repository
            </span>
            <span className="text-xs text-slate-400">Rule Engine Version Registry</span>
          </div>
          <h1 className="text-2xl font-bold text-white mt-1">Live Legal Metrology Rules Repository</h1>
          <p className="text-sm text-slate-300 mt-0.5">
            Full registry of packaged commodity regulations, condition schemas, and version lineage.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/admin/rules/notifications')}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-amber-600 hover:bg-amber-500 text-white shadow-md transition-all cursor-pointer"
          >
            🔔 Review Incoming Notifications &rarr;
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="glass-card p-4 space-y-3 border border-slate-800">
        <div className="flex flex-col md:flex-row items-center gap-3">
          {/* Search */}
          <div className="w-full md:flex-1">
            <input
              type="text"
              placeholder="Search by rule code, section reference, or keyword..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 rounded-xl bg-black border border-slate-700 text-xs text-white placeholder-slate-400 outline-none search-input"
              style={{ backgroundColor: '#000000', color: '#ffffff' }}
            />
          </div>

          {/* Category Filter */}
          <div className="w-full md:w-auto">
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full md:w-auto px-3 py-2 rounded-xl bg-black border border-slate-700 text-xs text-white outline-none dropdown-select"
              style={{ backgroundColor: '#000000', color: '#ffffff' }}
            >
              <option value="all" className="bg-black text-white">All Categories</option>
              <option value="general" className="bg-black text-white">General</option>
              <option value="food" className="bg-black text-white">Food & Beverages</option>
              <option value="electronics" className="bg-black text-white">Electronics</option>
              <option value="medical_device" className="bg-black text-white">Medical Devices</option>
              <option value="import" className="bg-black text-white">Imported Goods</option>
              <option value="ecommerce" className="bg-black text-white">E-Commerce</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="w-full md:w-auto flex items-center gap-1 bg-slate-900 p-1 rounded-xl border border-slate-800">
            {['all', 'in_force', 'draft', 'repealed'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-all cursor-pointer ${
                  statusFilter === st
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200'
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
        <div className="glass-card p-12 text-center text-slate-400 animate-pulse">
          Loading rules repository...
        </div>
      ) : error ? (
        <div className="glass-card p-6 text-red-400">
          Failed to load rules repository.
        </div>
      ) : rules.length === 0 ? (
        <div className="glass-card p-12 text-center text-slate-400">
          No rules matched the selected filter criteria.
        </div>
      ) : (
        <div className="glass-card overflow-hidden border border-slate-800">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider text-[11px] border-b border-slate-800">
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
              <tbody className="divide-y divide-slate-800/60">
                {rules.map((rule) => (
                  <tr key={rule.id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="px-4 py-3.5 font-mono font-bold text-indigo-300">
                      {rule.rule_id_code}
                      {rule.superseded_by_code && (
                        <div className="text-[10px] text-amber-400 font-sans font-normal mt-0.5">
                          Superseded by: {rule.superseded_by_code}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3.5 text-slate-200 max-w-xs">{rule.section_ref}</td>
                    <td className="px-4 py-3.5">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase font-semibold text-[10px]">
                        {rule.category}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-slate-400 font-mono text-[11px]">
                      {rule.effective_from} {rule.effective_to ? `to ${rule.effective_to}` : 'to present'}
                    </td>
                    <td className="px-4 py-3.5 font-mono text-emerald-400 text-[11px]">
                      {rule.condition?.type || 'required_field'}
                      {rule.condition?.field ? ` (${rule.condition.field})` : ''}
                    </td>
                    <td className="px-4 py-3.5">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                          rule.status === 'in_force'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                            : rule.status === 'draft'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        }`}
                      >
                        {rule.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <button
                        onClick={() => setSelectedRule(rule)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] cursor-pointer"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
          <div className="glass-card max-w-xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto border border-slate-700">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-indigo-400 font-bold">
                {selectedRule.rule_id_code}
              </span>
              <button
                onClick={() => setSelectedRule(null)}
                className="text-slate-400 hover:text-white text-lg font-bold cursor-pointer"
              >
                &times;
              </button>
            </div>

            <h3 className="text-base font-bold text-white">{selectedRule.section_ref}</h3>

            <div className="grid grid-cols-2 gap-3 text-xs p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <div>
                <span className="text-slate-500">Category:</span>
                <p className="text-white font-medium uppercase">{selectedRule.category}</p>
              </div>
              <div>
                <span className="text-slate-500">Status:</span>
                <p className="text-emerald-400 font-bold uppercase">{selectedRule.status}</p>
              </div>
              <div>
                <span className="text-slate-500">Effective From:</span>
                <p className="text-slate-300 font-mono">{selectedRule.effective_from}</p>
              </div>
              <div>
                <span className="text-slate-500">Effective To:</span>
                <p className="text-slate-300 font-mono">{selectedRule.effective_to || 'In Force'}</p>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">
                Condition Engine Schema (JSON)
              </label>
              <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs text-emerald-400 font-mono overflow-x-auto">
                {JSON.stringify(selectedRule.condition, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedRule(null)}
                className="px-4 py-2 rounded-xl text-xs font-medium bg-slate-800 text-slate-300 hover:bg-slate-700 cursor-pointer"
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
