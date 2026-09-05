import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { fetchInspectionQueue, type InspectionQueueItem } from '../api';
import StatusPill from '../../../components/ui/StatusPill';
import InspectionHistoryView from '../components/InspectionHistoryView';

export default function InspectionQueuePage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Active view synced with URL query param (?view=complaints | ?view=history)
  const currentView = searchParams.get('view') === 'history' ? 'history' : 'complaints';

  const [filterSource, setFilterSource] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const handleToggleView = (view: 'complaints' | 'history') => {
    setSearchParams({ view });
  };

  const { data: queueData = [], isLoading, error, refetch } = useQuery<InspectionQueueItem[]>({
    queryKey: ['inspection-queue'],
    queryFn: fetchInspectionQueue,
  });

  const queueList: InspectionQueueItem[] = Array.isArray(queueData)
    ? queueData
    : (queueData as { results?: InspectionQueueItem[] })?.results ?? [];

  const filteredQueue = queueList.filter((item) => {
    const matchesSource = filterSource === 'all' || item.source === filterSource;
    const productName = item.product_detail?.product_name ?? '';
    const brandName = item.product_detail?.brand_name ?? '';
    const barcode = item.product_detail?.gtin_barcode ?? '';
    const matchesSearch =
      !searchTerm ||
      productName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      brandName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      barcode.includes(searchTerm);
    return matchesSource && matchesSearch;
  });

  const getPriorityBadgeClass = (score: number) => {
    if (score >= 75) return 'bg-red-50 text-red-700 border-red-200';
    if (score >= 50) return 'bg-amber-50 text-amber-700 border-amber-200';
    return 'bg-blue-50 text-blue-700 border-blue-200';
  };

  const getSourceLabel = (source: string) => {
    switch (source) {
      case 'complaint':
        return { label: 'Citizen Complaint', icon: '📢', color: 'text-amber-700 border-amber-200 bg-amber-50' };
      case 'ecommerce_flag':
        return { label: 'E-commerce Flag', icon: '🛒', color: 'text-purple-700 border-purple-200 bg-purple-50' };
      default:
        return { label: 'Risk Engine', icon: '⚡', color: 'text-blue-700 border-blue-200 bg-blue-50' };
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--color-border)] pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">Field Officer Console</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
              Live Jurisdiction
            </span>
          </div>
          <p className="text-sm text-[var(--color-text-secondary)] mt-1">
            Prioritized Legal Metrology inspection targets, automated risk scores, and completed verification history.
          </p>
        </div>

        {/* Action button */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-muted)]">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span>State DB Synced</span>
          </div>
          <button
            onClick={() => navigate('/officer/capture')}
            className="px-4 py-2 rounded-lg text-sm font-semibold text-[var(--color-text-primary)] transition-colors shadow-sm flex items-center gap-2"
            style={{ background: 'var(--color-accent)' }}
          >
            <span>📷</span>
            <span>New inspection scan</span>
          </button>
        </div>
      </div>

      {/* Segmented Control Toggle */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="p-1 rounded-xl bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] inline-flex items-center gap-1 shadow-inner self-start">
          <button
            type="button"
            onClick={() => handleToggleView('complaints')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-2 ${
              currentView === 'complaints'
                ? 'text-white shadow-sm'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-secondary)]/60'
            }`}
            style={currentView === 'complaints' ? { background: 'var(--color-accent)' } : {}}
          >
            <span>📢</span>
            <span>Complaints Review</span>
            {queueList.length > 0 && (
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                  currentView === 'complaints'
                    ? 'bg-white/25 text-white'
                    : 'bg-[var(--color-border)] text-[var(--color-text-secondary)]'
                }`}
              >
                {queueList.length}
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => handleToggleView('history')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 flex items-center gap-2 ${
              currentView === 'history'
                ? 'text-white shadow-sm'
                : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-secondary)]/60'
            }`}
            style={currentView === 'history' ? { background: 'var(--color-accent)' } : {}}
          >
            <span>📋</span>
            <span>Inspection History</span>
          </button>
        </div>

        <div className="text-xs text-[var(--color-text-muted)] italic">
          {currentView === 'complaints'
            ? 'Pending citizen grievances & market targets awaiting inspection'
            : 'Historical inspection log with automated findings & statutory reports'}
        </div>
      </div>

      {/* View Switcher with smooth 200ms transition */}
      <div className="transition-opacity duration-200">
        {currentView === 'complaints' ? (
          /* ========================================================================= */
          /* View A: Complaints Review (100% functionality preserved)                  */
          /* ========================================================================= */
          <div className="space-y-6">
            {/* Filters & Search Bar */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2 relative">
                <input
                  type="text"
                  placeholder="Search by brand, product name, or GTIN barcode..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
                />
              </div>

              <div className="flex items-center gap-2">
                <label className="text-xs text-[var(--color-text-secondary)] whitespace-nowrap">Filter source:</label>
                <select
                  value={filterSource}
                  onChange={(e) => setFilterSource(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
                >
                  <option value="all">All Sources ({queueList.length})</option>
                  <option value="complaint">Citizen Complaints</option>
                  <option value="risk_engine">Risk Engine Prioritization</option>
                  <option value="ecommerce_flag">E-commerce Flagged</option>
                </select>
              </div>
            </div>

            {/* Queue List Content */}
            {isLoading ? (
              <div className="p-12 text-center text-[var(--color-text-muted)] glass-card">
                <div className="animate-spin text-3xl mb-3">⚙️</div>
                <p>Loading prioritized inspection queue from database...</p>
              </div>
            ) : error ? (
              <div className="p-6 bg-red-50 border border-red-200 rounded-lg text-red-700 flex items-center justify-between">
                <p>Failed to load inspection queue.</p>
                <button onClick={() => refetch()} className="px-3 py-1 bg-red-100 rounded text-xs">Retry</button>
              </div>
            ) : filteredQueue.length === 0 ? (
              <div className="p-12 text-center text-[var(--color-text-muted)] glass-card">
                <p className="text-base font-medium">No pending inspection targets found matching filter.</p>
                <p className="text-xs mt-1">All assigned market verification targets are up to date.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredQueue.map((item) => {
                  const sourceMeta = getSourceLabel(item.source);
                  return (
                    <div
                      key={item.id}
                      className="p-4 rounded-lg glass-card hover:border-[var(--color-accent)] transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                    >
                      {/* Left: Product & Source metadata */}
                      <div className="space-y-1.5 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-medium border ${sourceMeta.color}`}>
                            {sourceMeta.icon} {sourceMeta.label}
                          </span>
                          <span className={`px-2 py-0.5 rounded text-xs font-bold border ${getPriorityBadgeClass(item.priority_score)}`}>
                            Priority Risk: {item.priority_score.toFixed(1)}
                          </span>
                          <StatusPill verdict={item.status} />
                        </div>

                        <h3 className="text-base font-bold text-[var(--color-text-primary)]">
                          {item.product_detail?.brand_name ?? 'Target'} — {item.product_detail?.product_name ?? 'Market Inspection'}
                        </h3>

                        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[var(--color-text-muted)]">
                          <span>Barcode: <span className="font-mono text-[var(--color-text-secondary)]">{item.product_detail?.gtin_barcode ?? 'N/A'}</span></span>
                          <span>Category: <span className="capitalize">{item.product_detail?.category ?? 'general'}</span></span>
                          {item.complaint_detail && (
                            <span className="text-amber-600">
                              Location: {item.complaint_detail.location}
                            </span>
                          )}
                        </div>

                        {item.complaint_detail && (
                          <p className="text-xs text-[var(--color-text-muted)] bg-[var(--color-surface-tertiary)] p-2 rounded border border-[var(--color-border)] italic">
                            "{item.complaint_detail.description}"
                          </p>
                        )}
                      </div>

                      {/* Right: Actions */}
                      <div className="flex items-center gap-2 self-end md:self-center">
                        <button
                          onClick={() => navigate(`/officer/product/${item.product}/history`)}
                          className="px-3 py-2 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] hover:bg-gray-200 text-xs font-medium text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
                        >
                          History
                        </button>
                        <button
                          onClick={() =>
                            navigate('/officer/capture', {
                              state: {
                                barcode: item.product_detail?.gtin_barcode,
                                productId: item.product,
                                complaintId: item.complaint,
                                category: item.product_detail?.category,
                              },
                            })
                          }
                          className="px-4 py-2 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 text-[var(--color-text-primary)]"
                          style={{ background: 'var(--color-accent)' }}
                        >
                          <span>Start guided inspection</span>
                          <span>→</span>
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ) : (
          /* ========================================================================= */
          /* View B: Inspection History                                                */
          /* ========================================================================= */
          <InspectionHistoryView />
        )}
      </div>
    </div>
  );
}
