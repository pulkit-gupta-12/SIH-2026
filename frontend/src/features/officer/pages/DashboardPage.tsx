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

  const { data: queue = [], isLoading: isLoadingQueue } = useQuery<InspectionQueueItem[]>({
    queryKey: ['inspection-queue'],
    queryFn: fetchInspectionQueue,
    staleTime: 30_000,
  });

  const { data: cases = [], isLoading: isLoadingCases } = useQuery<EnforcementCaseResult[]>({
    queryKey: ['officer-cases-list'],
    queryFn: fetchOfficerCases,
    staleTime: 30_000,
  });

  const highPriorityTargets = queue.filter((q) => q.priority_score >= 75);
  const citizenComplaintsCount = queue.filter((q) => q.source === 'complaint').length;
  const section29Notices = cases.filter((c) => c.classification === 'first_time');
  const section39Penalties = cases.filter((c) => c.classification === 'repeat');

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-8 animate-fade-in">
      {/* Hero Header Card */}
      <div className="relative rounded-3xl p-6 md:p-8 overflow-hidden bg-gradient-to-br from-blue-950/80 via-slate-900 to-slate-950 border border-blue-500/20 shadow-2xl">
        <div className="absolute -right-6 -bottom-6 text-9xl opacity-10 select-none pointer-events-none">
          ⚖️
        </div>
        <div className="relative z-10 space-y-4 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30">
            <span>🛡️ Legal Metrology Enforcement Command</span>
          </div>
          <h1 className="text-2xl md:text-4xl font-extrabold text-white tracking-tight leading-tight">
            Field Officer Console
          </h1>
          <p className="text-sm text-slate-300 leading-relaxed">
            Execute guided on-site package verifications, inspect prioritized retail targets, review automated OCR rule verdicts, and issue statutory Section 29 Improvement Notices or Section 39 Penalty Cases.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <button
              onClick={() => navigate('/officer/queue')}
              className="px-5 py-3 rounded-xl font-bold text-white bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 shadow-lg shadow-blue-950/60 transition-all flex items-center gap-2"
            >
              <span>📋 View Inspection Queue ({queue.length})</span>
            </button>
            <button
              onClick={() => navigate('/officer/capture')}
              className="px-5 py-3 rounded-xl font-semibold text-slate-200 bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 transition-all flex items-center gap-2"
            >
              <span>📷 6-Step Guided Capture</span>
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Metric 1 */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Queue Targets</span>
            <span className="text-xl">📋</span>
          </div>
          <p className="text-3xl font-extrabold text-white">{queue.length}</p>
          <p className="text-xs text-slate-400 flex items-center gap-1">
            <span className="text-amber-400 font-semibold">{citizenComplaintsCount}</span> citizen complaints routed
          </p>
        </div>

        {/* Metric 2 */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">High Risk Priority</span>
            <span className="text-xl">⚡</span>
          </div>
          <p className="text-3xl font-extrabold text-rose-400">{highPriorityTargets.length}</p>
          <p className="text-xs text-slate-400">Score &ge; 75 requiring urgent check</p>
        </div>

        {/* Metric 3 */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Sec 29 Notices</span>
            <span className="text-xl">📜</span>
          </div>
          <p className="text-3xl font-extrabold text-amber-400">{section29Notices.length}</p>
          <p className="text-xs text-slate-400">30-day rectification windows</p>
        </div>

        {/* Metric 4 */}
        <div className="glass-card p-5 rounded-2xl border border-slate-800 bg-slate-900/40 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">Sec 39 Penalties</span>
            <span className="text-xl">🏛️</span>
          </div>
          <p className="text-3xl font-extrabold text-blue-400">{section39Penalties.length}</p>
          <p className="text-xs text-slate-400">Escalated to State Controller</p>
        </div>
      </div>

      {/* Action Hub Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Queue */}
        <div
          onClick={() => navigate('/officer/queue')}
          className="glass-card p-6 rounded-2xl border border-slate-800 hover:border-blue-500/40 cursor-pointer transition-all duration-200 group space-y-3"
        >
          <div className="w-12 h-12 rounded-xl bg-blue-500/15 text-blue-400 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
            🎯
          </div>
          <h3 className="font-bold text-base text-white group-hover:text-blue-400 transition-colors">
            Inspection Queue
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Access prioritized target list ranked by AI risk scoring, state jurisdiction filtering, and citizen complaints.
          </p>
        </div>

        {/* Card 2: Guided Capture */}
        <div
          onClick={() => navigate('/officer/capture')}
          className="glass-card p-6 rounded-2xl border border-slate-800 hover:border-emerald-500/40 cursor-pointer transition-all duration-200 group space-y-3"
        >
          <div className="w-12 h-12 rounded-xl bg-emerald-500/15 text-emerald-400 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
            📸
          </div>
          <h3 className="font-bold text-base text-white group-hover:text-emerald-400 transition-colors">
            Guided 6-Step Capture
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Multi-image statutory capture wizard with live quality checks, angle validation, and automated OCR processing.
          </p>
        </div>

        {/* Card 3: Case Creation */}
        <div
          onClick={() => navigate('/officer/case/new')}
          className="glass-card p-6 rounded-2xl border border-slate-800 hover:border-amber-500/40 cursor-pointer transition-all duration-200 group space-y-3"
        >
          <div className="w-12 h-12 rounded-xl bg-amber-500/15 text-amber-400 flex items-center justify-center text-2xl group-hover:scale-110 transition-transform">
            ⚖️
          </div>
          <h3 className="font-bold text-base text-white group-hover:text-amber-400 transition-colors">
            Enforcement & Statutory Cases
          </h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Generate formal Section 29 Improvement Notices or escalate Section 39 repeat offenses with audit trails.
          </p>
        </div>
      </div>

      {/* Live Priority Queue & Recent Cases Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Priority Targets */}
        <div className="glass-card p-6 rounded-2xl border border-slate-800/80 bg-slate-900/40 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>⚡</span>
              <span>Priority Inspection Targets</span>
            </h3>
            <button
              onClick={() => navigate('/officer/queue')}
              className="text-xs text-blue-400 hover:underline font-semibold"
            >
              View Full Queue →
            </button>
          </div>

          {isLoadingQueue ? (
            <p className="text-xs text-slate-400 text-center py-4">Loading queue items...</p>
          ) : queue.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-4">No inspection targets in queue.</p>
          ) : (
            <div className="space-y-3">
              {queue.slice(0, 4).map((item) => (
                <div
                  key={item.id}
                  onClick={() => navigate(`/officer/capture?productId=${item.product}&targetId=${item.id}`)}
                  className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/60 hover:border-blue-500/40 cursor-pointer transition-all flex items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white truncate">{item.product_detail.brand_name} — {item.product_detail.product_name}</span>
                    </div>
                    <p className="text-slate-400 text-[11px] truncate">
                      Source: {item.source === 'complaint' ? '📢 Citizen Complaint' : '⚡ Risk Engine'} • GTIN: {item.product_detail.gtin_barcode}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="px-2 py-0.5 rounded-full font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                      Score: {item.priority_score.toFixed(0)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Active Enforcement Cases */}
        <div className="glass-card p-6 rounded-2xl border border-slate-800/80 bg-slate-900/40 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>📜</span>
              <span>Active Enforcement Cases</span>
            </h3>
            <button
              onClick={() => navigate('/officer/case/new')}
              className="text-xs text-blue-400 hover:underline font-semibold"
            >
              + File New Case
            </button>
          </div>

          {isLoadingCases ? (
            <p className="text-xs text-slate-400 text-center py-4">Loading active cases...</p>
          ) : cases.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-4">No active enforcement cases found.</p>
          ) : (
            <div className="space-y-3">
              {cases.slice(0, 4).map((c) => (
                <div
                  key={c.id}
                  onClick={() => navigate(`/officer/product/${c.product}/history`)}
                  className="p-3 rounded-xl bg-slate-800/40 border border-slate-700/60 hover:border-amber-500/40 cursor-pointer transition-all flex items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white">Case #{c.id}: {c.brand_name}</span>
                    </div>
                    <p className="text-slate-400 text-[11px] truncate">
                      {c.classification === 'first_time' ? 'Sec 29 Improvement Notice' : 'Sec 39 Penalty Case'} • Status: {c.status}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      c.classification === 'first_time'
                        ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                        : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
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
