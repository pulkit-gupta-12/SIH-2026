import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchProcessingResult, type ScanProcessingResult } from '../api';
import StatusPill from '../../../components/ui/StatusPill';

export default function ProcessingResultPage() {
  const { scanId } = useParams<{ scanId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const stateScanData = location.state?.scanData as ScanProcessingResult | undefined;

  const { data: scan, isLoading, error } = useQuery<ScanProcessingResult>({
    queryKey: ['scan-processing-result', scanId],
    queryFn: () => fetchProcessingResult(scanId || '0'),
    initialData: stateScanData,
    enabled: Boolean(scanId),
  });

  if (isLoading) {
    return (
      <div className="p-16 text-center text-muted-foreground glass-card rounded-2xl border border-border/50">
        <div className="animate-spin text-4xl mb-3">⚙️</div>
        <h2 className="text-lg font-bold text-foreground">Processing OCR Extraction & Rules Engine...</h2>
        <p className="text-xs text-muted-foreground mt-1">Analyzing font sizes, declaration zones, and statutory PCR mandates.</p>
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="p-8 glass-card rounded-2xl border border-rose-500/30 text-rose-300 space-y-3">
        <h2 className="text-lg font-bold">Failed to load scan processing results.</h2>
        <button onClick={() => navigate('/officer/queue')} className="px-4 py-2 bg-card border rounded-lg text-xs">
          ← Return to Inspection Queue
        </button>
      </div>
    );
  }

  const check = scan.compliance_check;
  const isNonCompliant = check?.verdict === 'non_compliant';

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs font-semibold">
              Inspection Scan #{scan.id}
            </span>
            <span className="text-xs text-muted-foreground">Capture Method: {scan.capture_method}</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground mt-1">Automated Processing & Rule Evaluation Result</h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/officer/queue')}
            className="px-3.5 py-2 rounded-lg bg-card/60 border border-border text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            Queue
          </button>
          {check && (
            <button
              onClick={() => navigate(`/officer/check/${check.id}/review`, { state: { scan } })}
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 transition-all flex items-center gap-1.5 shadow-md"
            >
              <span>Review Findings & Confirm</span>
              <span>→</span>
            </button>
          )}
        </div>
      </div>

      {/* High-Level Verdict Summary Banner */}
      {check && (
        <div
          className={`p-6 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-4 ${
            isNonCompliant
              ? 'bg-rose-500/10 border-rose-500/30 text-rose-200'
              : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-200'
          }`}
        >
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <StatusPill verdict={check.verdict} />
              <span className="text-xs font-mono opacity-80">
                Confidence: {Math.round((check.overall_confidence || 0.95) * 100)}%
              </span>
            </div>
            <h2 className="text-xl font-bold text-foreground mt-2">
              {isNonCompliant
                ? `Flagged ${check.violations.length} Regulatory Non-Compliance Issue(s)`
                : 'All Package Declarations Meet Statutory Standards'}
            </h2>
            <p className="text-xs text-muted-foreground">
              Evaluated against Gazette Rule Set as of {new Date(check.evaluated_against_rule_set_date).toLocaleDateString()}
            </p>
          </div>

          <div className="flex items-center gap-2 self-start md:self-center">
            {check.reviewed_by_officer ? (
              <span className="px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-semibold">
                ✓ Reviewed by {check.reviewed_by_officer_username}
              </span>
            ) : (
              <span className="px-3 py-1.5 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/40 text-xs font-semibold animate-pulse">
                Pending Officer Review
              </span>
            )}
          </div>
        </div>
      )}

      {/* Two Columns: Extracted OCR Fields vs Rule Violations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Extracted Fields Table */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <span>🔍</span>
              <span>OCR Extracted Fields ({scan.extracted_fields.length})</span>
            </h3>
            <span className="text-[11px] text-muted-foreground">Vision OCR + Metric Calibration</span>
          </div>

          <div className="rounded-xl glass-card border border-border/60 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-muted/40 text-muted-foreground font-semibold border-b border-border/50">
                  <tr>
                    <th className="p-3">Field Type</th>
                    <th className="p-3">Extracted Text</th>
                    <th className="p-3">Font Height</th>
                    <th className="p-3">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 font-mono">
                  {scan.extracted_fields.length === 0 ? (
                    <tr>
                      <td colSpan={4} className="p-4 text-center text-muted-foreground">
                        No fields extracted
                      </td>
                    </tr>
                  ) : (
                    scan.extracted_fields.map((f) => (
                      <tr key={f.id} className="hover:bg-muted/20">
                        <td className="p-3 font-semibold text-foreground capitalize">
                          {f.field_type.replace('_', ' ')}
                        </td>
                        <td className="p-3 text-foreground/90 font-sans">{f.extracted_value}</td>
                        <td className="p-3 text-muted-foreground">
                          {f.font_size_mm ? `${f.font_size_mm} mm` : '—'}
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                              f.confidence_score >= 0.9
                                ? 'bg-emerald-500/20 text-emerald-300'
                                : 'bg-amber-500/20 text-amber-300'
                            }`}
                          >
                            {Math.round(f.confidence_score * 100)}%
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Statutory Rule Evaluations & Violations */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
              <span>⚖️</span>
              <span>Statutory Rule Evaluations ({check?.violations.length || 0})</span>
            </h3>
            <span className="text-[11px] text-muted-foreground">Rules Engine v2.0</span>
          </div>

          <div className="space-y-3">
            {!check?.violations || check.violations.length === 0 ? (
              <div className="p-6 rounded-xl glass-card border border-emerald-500/30 text-center space-y-1">
                <div className="text-2xl text-emerald-400">✓</div>
                <p className="text-xs font-semibold text-foreground">Zero Violations Found</p>
                <p className="text-[11px] text-muted-foreground">All mandatory statements are present, legible, and compliant.</p>
              </div>
            ) : (
              check.violations.map((v) => (
                <div
                  key={v.id}
                  className="p-4 rounded-xl glass-card border border-rose-500/40 space-y-2 hover:border-rose-500 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/30">
                        {v.rule_id_code}
                      </span>
                      <span className="text-xs text-muted-foreground">{v.section_ref}</span>
                    </div>

                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                        v.is_first_time
                          ? 'bg-blue-500/20 text-blue-300 border-blue-500/30'
                          : 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                      }`}
                    >
                      {v.is_first_time ? '1st-Time Procedural' : 'Repeat Offense'}
                    </span>
                  </div>

                  <p className="text-xs text-foreground/90 font-medium leading-relaxed">{v.description}</p>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
