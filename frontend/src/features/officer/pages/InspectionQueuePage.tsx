import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { fetchInspectionQueue, type InspectionQueueItem } from '../api';
import StatusPill from '../../../components/ui/StatusPill';

export default function InspectionQueuePage() {
  const navigate = useNavigate();
  const [filterSource, setFilterSource] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const { data: queue = [], isLoading, error, refetch } = useQuery<InspectionQueueItem[]>({
    queryKey: ['inspection-queue'],
    queryFn: fetchInspectionQueue,
  });

  const filteredQueue = queue.filter((item) => {
    const matchesSource = filterSource === 'all' || item.source === filterSource;
    const matchesSearch =
      !searchTerm ||
      item.product_detail.product_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.product_detail.brand_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.product_detail.gtin_barcode.includes(searchTerm);
    return matchesSource && matchesSearch;
  });

  const getPriorityBadgeClass = (score: number) => {
    if (score >= 75) return 'bg-rose-500/20 text-rose-300 border-rose-500/30';
    if (score >= 50) return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
    return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
  };

  const getSourceLabel = (source: string) => {
    switch (source) {
      case 'complaint':
        return { label: 'Citizen Complaint', icon: '📢', color: 'text-amber-400 border-amber-500/30 bg-amber-500/10' };
      case 'ecommerce_flag':
        return { label: 'E-commerce Flag', icon: '🛒', color: 'text-purple-400 border-purple-500/30 bg-purple-500/10' };
      default:
        return { label: 'Risk Engine', icon: '⚡', color: 'text-blue-400 border-blue-500/30 bg-blue-500/10' };
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-foreground">Field Inspection Queue</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/20 text-primary border border-primary/30">
              Live Jurisdiction
            </span>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Prioritized Legal Metrology inspection targets, automated risk scores, and routed citizen grievances.
          </p>
        </div>

        {/* Action button */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card/60 border border-border/50 text-xs text-muted-foreground">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>State DB Synced</span>
          </div>
          <button
            onClick={() => navigate('/officer/capture')}
            className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary/90 transition-all shadow-md flex items-center gap-2"
          >
            <span>📷</span>
            <span>New Inspection Scan</span>
          </button>
        </div>
      </div>

      {/* Filters & Search Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2 relative">
          <input
            type="text"
            placeholder="Search by brand, product name, or GTIN barcode..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2.5 rounded-lg bg-card/60 border border-border text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-muted-foreground whitespace-nowrap">Filter Source:</label>
          <select
            value={filterSource}
            onChange={(e) => setFilterSource(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-card/60 border border-border text-foreground text-sm focus:outline-none focus:ring-2 focus:ring-primary/40"
          >
            <option value="all">All Sources ({queue.length})</option>
            <option value="complaint">Citizen Complaints</option>
            <option value="risk_engine">Risk Engine Prioritization</option>
            <option value="ecommerce_flag">E-commerce Flagged</option>
          </select>
        </div>
      </div>

      {/* Queue List Content */}
      {isLoading ? (
        <div className="p-12 text-center text-muted-foreground glass-card rounded-xl border border-border/50">
          <div className="animate-spin text-3xl mb-3">⚙️</div>
          <p>Loading prioritized inspection queue from PostgreSQL...</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 flex items-center justify-between">
          <p>Failed to load inspection queue.</p>
          <button onClick={() => refetch()} className="px-3 py-1 bg-rose-500/20 rounded text-xs">Retry</button>
        </div>
      ) : filteredQueue.length === 0 ? (
        <div className="p-12 text-center text-muted-foreground glass-card rounded-xl border border-border/50">
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
                className="p-4 rounded-xl glass-card border border-border/60 hover:border-primary/40 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
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

                  <h3 className="text-base font-bold text-foreground">
                    {item.product_detail.brand_name} — {item.product_detail.product_name}
                  </h3>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                    <span>Barcode: <span className="font-mono text-foreground/80">{item.product_detail.gtin_barcode}</span></span>
                    <span>Category: <span className="capitalize">{item.product_detail.category}</span></span>
                    {item.complaint_detail && (
                      <span className="text-amber-300">
                        Location: {item.complaint_detail.location}
                      </span>
                    )}
                  </div>

                  {item.complaint_detail && (
                    <p className="text-xs text-muted-foreground bg-black/20 p-2 rounded border border-border/30 italic">
                      "{item.complaint_detail.description}"
                    </p>
                  )}
                </div>

                {/* Right: Actions */}
                <div className="flex items-center gap-2 self-end md:self-center">
                  <button
                    onClick={() => navigate(`/officer/product/${item.product}/history`)}
                    className="px-3 py-2 rounded-lg bg-card/60 border border-border/60 hover:bg-card text-xs font-medium text-muted-foreground hover:text-foreground transition-all"
                  >
                    History
                  </button>
                  <button
                    onClick={() =>
                      navigate('/officer/capture', {
                        state: {
                          barcode: item.product_detail.gtin_barcode,
                          productId: item.product,
                          complaintId: item.complaint,
                          category: item.product_detail.category,
                        },
                      })
                    }
                    className="px-4 py-2 rounded-lg bg-primary/20 hover:bg-primary text-primary hover:text-primary-foreground border border-primary/40 text-xs font-semibold transition-all flex items-center gap-1.5"
                  >
                    <span>Start Guided Inspection</span>
                    <span>→</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
