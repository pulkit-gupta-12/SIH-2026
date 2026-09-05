import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  fetchInspectionQueue,
  fetchOfficerCases,
  type InspectionQueueItem,
  type EnforcementCaseResult,
} from '../api';

export default function OfficerDashboardPage() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSource, setFilterSource] = useState('all');

  const { data: queueData = [], isLoading: isLoadingQueue } = useQuery<InspectionQueueItem[]>({
    queryKey: ['inspection-queue'],
    queryFn: fetchInspectionQueue,
    staleTime: 30_000,
  });

  const { data: casesData = [], isLoading: isLoadingCases } = useQuery<EnforcementCaseResult[]>({
    queryKey: ['officer-cases-list'],
    queryFn: fetchOfficerCases,
    staleTime: 30_000,
  });

  const queue: InspectionQueueItem[] = Array.isArray(queueData)
    ? queueData
    : (queueData as { results?: InspectionQueueItem[] })?.results ?? [];

  const cases: EnforcementCaseResult[] = Array.isArray(casesData)
    ? casesData
    : (casesData as { results?: EnforcementCaseResult[] })?.results ?? [];

  const highPriorityTargets = queue.filter((q) => (q.priority_score ?? 0) >= 75);
  const citizenComplaintsCount = queue.filter((q) => q.source === 'complaint').length;
  const section29Notices = cases.filter((c) => c.classification === 'first_time');
  const section39Penalties = cases.filter((c) => c.classification === 'repeat');

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-6 animate-fade-in">
      {/* Hero Header Card */}
      <div className="glass-card card-accent-left p-6 md:p-8">
        <div className="space-y-4 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
            <span>🛡️ Legal Metrology Enforcement Command</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text-primary)] tracking-tight leading-tight">
            Field Officer Console
          </h1>
          <p className="text-sm text-[var(--color-text-secondary)] leading-relaxed">
            Execute guided on-site package verifications, inspect prioritized retail targets, review automated OCR rule verdicts, and issue statutory Section 29 Improvement Notices or Section 39 Penalty Cases.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <button
              onClick={() => navigate('/officer/queue')}
              className="px-5 py-3 rounded-lg font-semibold text-[var(--color-text-primary)] transition-colors flex items-center gap-2"
              style={{ background: 'linear-gradient(135deg, #e8730c, #d4670a)' }}
            >
              <span>📋 View inspection queue ({queue.length})</span>
            </button>
            <button
              onClick={() => navigate('/officer/capture')}
              className="px-5 py-3 rounded-lg font-semibold text-[var(--color-text-secondary)] bg-[var(--color-surface-tertiary)] hover:bg-gray-200 border border-[var(--color-border)] transition-colors flex items-center gap-2"
            >
              <span>📷 6-step guided capture</span>
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="glass-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[var(--color-text-muted)] font-medium">Queue targets</span>
            <span className="w-10 h-10 rounded-lg bg-[var(--color-accent-subtle)] flex items-center justify-center text-xl">📋</span>
          </div>
          <p className="text-3xl font-bold text-[var(--color-text-primary)]">{queue.length}</p>
          <p className="text-xs text-[var(--color-text-muted)] flex items-center gap-1">
            <span className="text-amber-600 font-semibold">{citizenComplaintsCount}</span> citizen complaints routed
          </p>
        </div>

        {/* Metric 2 */}
        <div className="glass-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[var(--color-text-muted)] font-medium">High risk priority</span>
            <span className="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center text-xl">⚡</span>
          </div>
          <p className="text-3xl font-bold text-red-600">{highPriorityTargets.length}</p>
          <p className="text-xs text-[var(--color-text-muted)]">Score &ge; 75 requiring urgent check</p>
        </div>

        {/* Metric 3 */}
        <div className="glass-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[var(--color-text-muted)] font-medium">Sec 29 notices</span>
            <span className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center text-xl">📜</span>
          </div>
          <p className="text-3xl font-bold text-amber-600">{section29Notices.length}</p>
          <p className="text-xs text-[var(--color-text-muted)]">30-day rectification windows</p>
        </div>

        {/* Metric 4 */}
        <div className="glass-card p-5 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-[var(--color-text-muted)] font-medium">Sec 39 penalties</span>
            <span className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-xl">🏛️</span>
          </div>
          <p className="text-3xl font-bold text-blue-600">{section39Penalties.length}</p>
          <p className="text-xs text-[var(--color-text-muted)]">Escalated to State Controller</p>
        </div>
      </div>

      {/* Action Hub Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Queue */}
        <div
          onClick={() => navigate('/officer/queue')}
          className="glass-card p-6 hover:border-[var(--color-accent)] cursor-pointer transition-all duration-150 group space-y-3 hover:shadow-md hover:-translate-y-px"
        >
          <div className="w-12 h-12 rounded-lg bg-[var(--color-accent-subtle)] text-[var(--color-accent)] flex items-center justify-center text-2xl group-hover:scale-105 transition-transform">
            🎯
          </div>
          <h3 className="font-bold text-base text-[var(--color-text-primary)] group-hover:text-[var(--color-accent)] transition-colors">
            Inspection queue
          </h3>
          <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
            Access prioritized target list ranked by AI risk scoring, state jurisdiction filtering, and citizen complaints.
          </p>
        </div>

        {/* Card 2: Guided Capture */}
        <div
          onClick={() => navigate('/officer/capture')}
          className="glass-card p-6 hover:border-green-300 cursor-pointer transition-all duration-150 group space-y-3 hover:shadow-md hover:-translate-y-px"
        >
          <div className="w-12 h-12 rounded-lg bg-green-50 text-green-600 flex items-center justify-center text-2xl group-hover:scale-105 transition-transform">
            📸
          </div>
          <h3 className="font-bold text-base text-[var(--color-text-primary)] group-hover:text-green-600 transition-colors">
            Guided 6-step capture
          </h3>
          <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
            Multi-image statutory capture wizard with live quality checks, angle validation, and automated OCR processing.
          </p>
        </div>

        {/* Card 3: Case Creation */}
        <div
          onClick={() => navigate('/officer/case/new')}
          className="glass-card p-6 hover:border-amber-300 cursor-pointer transition-all duration-150 group space-y-3 hover:shadow-md hover:-translate-y-px"
        >
          <div className="w-12 h-12 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center text-2xl group-hover:scale-105 transition-transform">
            ⚖️
          </div>
          <h3 className="font-bold text-base text-[var(--color-text-primary)] group-hover:text-amber-600 transition-colors">
            Enforcement and statutory cases
          </h3>
          <p className="text-xs text-[var(--color-text-muted)] leading-relaxed">
            Generate formal Section 29 Improvement Notices or escalate Section 39 repeat offenses with audit trails.
          </p>
        </div>
      </div>

      {/* Quick Search & Filter Controls */}
      <div className="glass-card p-4 space-y-3">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--color-text-muted)] text-sm pointer-events-none">🔍</span>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search targets or cases by brand, product name, or GTIN..."
              className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors font-mono"
            />
          </div>

          <div className="w-full sm:w-auto">
            <select
              value={filterSource}
              onChange={(e) => setFilterSource(e.target.value)}
              className="w-full sm:w-auto px-4 py-2.5 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
            >
              <option value="all">All Sources ({queue.length})</option>
              <option value="complaint">Citizen Complaints</option>
              <option value="risk_engine">Risk Engine Prioritization</option>
              <option value="ecommerce_flag">E-commerce Flagged</option>
            </select>
          </div>
        </div>
      </div>

      {/* Live Priority Queue & Recent Cases Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Priority Targets */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-3">
            <h3 className="text-sm font-bold text-[var(--color-text-primary)] flex items-center gap-2">
              <span>⚡</span>
              <span>Priority inspection targets</span>
            </h3>
            <button
              onClick={() => navigate('/officer/queue')}
              className="text-xs text-[var(--color-accent)] hover:underline font-semibold"
            >
              View full queue →
            </button>
          </div>

          {isLoadingQueue ? (
            <p className="text-xs text-[var(--color-text-muted)] text-center py-4">Loading queue items...</p>
          ) : queue.length === 0 ? (
            <p className="text-xs text-[var(--color-text-muted)] text-center py-4">No inspection targets in queue.</p>
          ) : (
            <div className="space-y-3">
              {queue
                .filter((item) => {
                  const matchesSearch =
                    !searchTerm ||
                    (item.product_detail?.product_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                    (item.product_detail?.brand_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                    (item.product_detail?.gtin_barcode || '').toLowerCase().includes(searchTerm.toLowerCase());
                  const matchesSource = filterSource === 'all' || item.source === filterSource;
                  return matchesSearch && matchesSource;
                })
                .slice(0, 4)
                .map((item) => (
                <div
                  key={item.id}
                  onClick={() => navigate(`/officer/capture?productId=${item.product}&targetId=${item.id}`)}
                  className="p-3 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] hover:border-[var(--color-accent)] cursor-pointer transition-all flex items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[var(--color-text-primary)] truncate">
                        {item.product_detail?.brand_name ?? 'Target'} — {item.product_detail?.product_name ?? 'Inspection Item'}
                      </span>
                    </div>
                    <p className="text-[var(--color-text-muted)] text-[11px] truncate">
                      Source: {item.source === 'complaint' ? '📢 Citizen Complaint' : '⚡ Risk Engine'} • GTIN: {item.product_detail?.gtin_barcode ?? 'N/A'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="px-2 py-0.5 rounded-full font-bold bg-red-50 text-red-600 border border-red-200">
                      Score: {item.priority_score.toFixed(0)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Active Enforcement Cases */}
        <div className="glass-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--color-border)] pb-3">
            <h3 className="text-sm font-bold text-[var(--color-text-primary)] flex items-center gap-2">
              <span>📜</span>
              <span>Active enforcement cases</span>
            </h3>
            <button
              onClick={() => navigate('/officer/case/new')}
              className="text-xs text-[var(--color-accent)] hover:underline font-semibold"
            >
              + File new case
            </button>
          </div>

          {isLoadingCases ? (
            <p className="text-xs text-[var(--color-text-muted)] text-center py-4">Loading active cases...</p>
          ) : cases.length === 0 ? (
            <p className="text-xs text-[var(--color-text-muted)] text-center py-4">No active enforcement cases found.</p>
          ) : (
            <div className="space-y-3">
              {cases
                .filter((c) => {
                  return (
                    !searchTerm ||
                    (c.brand_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                    (c.product_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                    (c.gtin_barcode || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                    `Case #${c.id}`.toLowerCase().includes(searchTerm.toLowerCase())
                  );
                })
                .slice(0, 4)
                .map((c) => (
                <div
                  key={c.id}
                  onClick={() => navigate(`/officer/product/${c.product}/history`)}
                  className="p-3 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] hover:border-amber-300 cursor-pointer transition-all flex items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-[var(--color-text-primary)]">Case #{c.id}: {c.brand_name}</span>
                    </div>
                    <p className="text-[var(--color-text-muted)] text-[11px] truncate">
                      {c.classification === 'first_time' ? 'Sec 29 Improvement Notice' : 'Sec 39 Penalty Case'} • Status: {c.status}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      c.classification === 'first_time'
                        ? 'bg-amber-50 text-amber-700 border border-amber-200'
                        : 'bg-red-50 text-red-700 border border-red-200'
                    }`}
                  >
                    {c.classification === 'first_time' ? 'Sec 29' : 'Sec 39'}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
