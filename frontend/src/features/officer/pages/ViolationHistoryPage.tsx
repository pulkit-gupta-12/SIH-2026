import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchProductViolationHistory, type ProductViolationTimeline } from '../api';

export default function ViolationHistoryPage() {
  const { productId } = useParams<{ productId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const violationId = searchParams.get('violationId');

  const { data: timeline, isLoading, error } = useQuery<ProductViolationTimeline>({
    queryKey: ['product-violation-history', productId],
    queryFn: () => fetchProductViolationHistory(productId || '0'),
    enabled: Boolean(productId),
  });

  if (isLoading) {
    return (
      <div className="p-16 text-center text-muted-foreground glass-card rounded-2xl border border-border/50">
        <div className="animate-spin text-3xl mb-3">⚖️</div>
        <p className="text-sm">Loading statutory violation history & timeline...</p>
      </div>
    );
  }

  if (error || !timeline) {
    return (
      <div className="p-8 glass-card rounded-2xl border border-rose-500/30 text-rose-300 space-y-3">
        <h2 className="text-lg font-bold">Failed to load product violation history.</h2>
        <button onClick={() => navigate(-1)} className="px-4 py-2 bg-card border rounded-lg text-xs">
          ← Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/20 text-primary border border-primary/30">
              Statutory Compliance History
            </span>
            <span className="text-xs text-muted-foreground font-mono">GTIN: {timeline.gtin_barcode}</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground mt-1">
            {timeline.brand_name} — {timeline.product_name}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="px-3.5 py-2 rounded-lg bg-card/60 border border-border text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            ← Back
          </button>
          <button
            onClick={() => navigate(`/officer/case/new?product=${timeline.product_id}${violationId ? `&violation=${violationId}` : ''}`)}
            className="px-4 py-2 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90 shadow-md flex items-center gap-2"
          >
            <span>⚖️</span>
            <span>Initiate Enforcement Case</span>
          </button>
        </div>
      </div>

      {/* Offense Summary Classification Card */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card p-5 rounded-2xl border border-border/50 bg-card/40 space-y-1">
          <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Total Violations Recorded</span>
          <p className="text-3xl font-extrabold text-foreground">{timeline.total_violations}</p>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-border/50 bg-card/40 space-y-1">
          <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Offense Classification</span>
          <div className="flex items-center gap-2 pt-1">
            {timeline.has_repeat_offenses ? (
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                ⚠️ Repeat Offender (Section 39 Penalty)
              </span>
            ) : timeline.total_violations > 0 ? (
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                1st Offense (Section 29 Notice)
              </span>
            ) : (
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                Clean Compliance Record
              </span>
            )}
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl border border-border/50 bg-card/40 space-y-1">
          <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Statutory Procedure</span>
          <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
            {timeline.has_repeat_offenses
              ? 'Repeat violations mandate immediate Section 39 compounding penalty escalation to the State Controller.'
              : 'First-time non-compliance initiates a Section 29 30-day statutory rectification improvement notice.'}
          </p>
        </div>
      </div>

      {/* Timeline Section */}
      <div className="glass-card p-6 rounded-2xl border border-border/60 bg-card/50 space-y-6">
        <div className="flex items-center justify-between border-b border-border/40 pb-3">
          <h2 className="text-base font-bold text-foreground flex items-center gap-2">
            <span>📜</span>
            <span>Chronological Violation History</span>
          </h2>
          <span className="text-xs text-muted-foreground font-medium">
            {timeline.history.length} Event{timeline.history.length === 1 ? '' : 's'}
          </span>
        </div>

        {timeline.history.length === 0 ? (
          <div className="p-8 text-center text-muted-foreground border border-dashed border-border/60 rounded-xl">
            <span className="text-3xl block mb-2">✅</span>
            <p className="text-sm font-medium text-foreground">No prior violations found for this commodity.</p>
            <p className="text-xs text-muted-foreground mt-1">This product has maintained statutory compliance in past inspections.</p>
          </div>
        ) : (
          <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-border">
            {timeline.history.map((event, index) => (
              <div key={event.id || index} className="relative space-y-2 group">
                {/* Dot */}
                <div
                  className={`absolute -left-6 top-1.5 w-5 h-5 rounded-full border-2 bg-card flex items-center justify-center text-[10px] ${
                    event.is_first_time
                      ? 'border-amber-400 text-amber-400'
                      : 'border-rose-500 text-rose-400 font-bold'
                  }`}
                >
                  {index + 1}
                </div>

                <div className="glass-card p-4 rounded-xl border border-border/60 bg-card/70 hover:border-primary/40 transition-all space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-primary/10 text-primary border border-primary/20">
                        {event.rule_id_code}
                      </span>
                      <span className="text-xs text-muted-foreground font-semibold">{event.section_ref}</span>
                      {event.is_first_time ? (
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                          1st Offense
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                          ⚠️ Repeat Offense
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground font-mono">
                      {event.created_at ? new Date(event.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }) : 'Recorded'}
                    </span>
                  </div>

                  <p className="text-sm text-foreground leading-relaxed">{event.description}</p>

                  <div className="flex items-center justify-between pt-2 border-t border-border/40 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground">Enforcement Status:</span>
                      {event.case_id ? (
                        <span className="font-semibold text-primary">Case #{event.case_id} ({event.case_status || 'Active'})</span>
                      ) : (
                        <span className="text-amber-400">Pending Case Filing</span>
                      )}
                    </div>
                    {!event.case_id && (
                      <button
                        onClick={() => navigate(`/officer/case/new?product=${timeline.product_id}&violation=${event.violation_id}`)}
                        className="px-3 py-1 rounded bg-primary/20 text-primary hover:bg-primary/30 border border-primary/30 font-semibold transition-all"
                      >
                        File Case →
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
