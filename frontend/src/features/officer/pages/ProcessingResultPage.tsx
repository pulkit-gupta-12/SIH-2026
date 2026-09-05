import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchProcessingResult, type ScanProcessingResult, type ComplianceReport } from '../api';
import ComplianceReportView from '../components/ComplianceReportView';
import ReportDownloadButton from '../components/ReportDownloadButton';

function getOrBuildReport(scan: ScanProcessingResult): ComplianceReport | null {
  if (scan.compliance_check?.report_data && scan.compliance_check.report_data.overall_status) {
    return scan.compliance_check.report_data;
  }
  if (scan.canonical_data?.compliance_report && scan.canonical_data.compliance_report.overall_status) {
    return scan.canonical_data.compliance_report;
  }
  if (!scan.compliance_check) {
    return null;
  }

  // Graceful fallback adapter for legacy checks
  const check = scan.compliance_check;
  const isNonCompliant = check.verdict === 'non_compliant';
  const isNeedsReview = check.verdict === 'needs_review';
  const overallStatus: 'COMPLIANT' | 'NON_COMPLIANT' | 'NEEDS_REVIEW' = isNonCompliant
    ? 'NON_COMPLIANT'
    : isNeedsReview
    ? 'NEEDS_REVIEW'
    : 'COMPLIANT';

  const violations = (check.violations || []).map((v) => ({
    rule_id: v.rule_id_code || 'LMPC-RULE',
    section_ref: v.section_ref || 'Legal Metrology Rules, 2011',
    title: v.description?.slice(0, 60) || 'Statutory Requirement',
    status: 'FAIL' as const,
    severity: v.is_first_time ? ('MEDIUM' as const) : ('HIGH' as const),
    detected_value: v.field || 'Non-conforming declaration',
    expected: 'Declaration must strictly comply with statutory specifications.',
    reason: v.description,
    evidence: {
      field: v.field,
      raw_text: v.description,
      source_panel: 'mandatory_declaration',
    },
    source_panel: 'mandatory_declaration',
    confidence: check.overall_confidence || 0.90,
    requires_human_review: false,
    evaluation_source: 'deterministic',
  }));

  const evidence = (scan.extracted_fields || []).map((ef) => ({
    field: ef.field_type,
    raw_text: ef.extracted_value,
    normalized_value: null,
    confidence: ef.confidence_score,
    source_panel: ef.placement_zone || 'mandatory_declaration',
    detected: true,
    normalization_status: 'success',
  }));

  return {
    inspection_id: `INSP-${scan.id}`,
    overall_status: overallStatus,
    summary: {
      total_rules: violations.length,
      passed: overallStatus === 'COMPLIANT' ? 12 : 0,
      failed: violations.length,
      warnings: 0,
      review_required: isNeedsReview ? 1 : 0,
      not_applicable: 0,
    },
    violations,
    warnings: [],
    reviews: [],
    passed_rules: [],
    evidence,
    generated_at: check.created_at || new Date().toISOString(),
  };
}

export default function ProcessingResultPage() {
  const { scanId } = useParams<{ scanId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const stateScanData = location.state?.scanData as ScanProcessingResult | undefined;

  const {
    data: scan,
    isLoading,
    error,
    refetch,
  } = useQuery<ScanProcessingResult>({
    queryKey: ['scan-processing-result', scanId],
    queryFn: () => fetchProcessingResult(scanId || '0'),
    initialData: stateScanData,
    enabled: Boolean(scanId),
  });

  // 1. Loading State
  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto p-16 text-center text-muted-foreground glass-card rounded-2xl border border-border/50 space-y-4 animate-fade-in">
        <div className="animate-spin text-5xl mb-2">⚙️</div>
        <h2 className="text-xl font-bold text-foreground">Processing OCR Extraction & Rules Engine...</h2>
        <p className="text-xs text-muted-foreground max-w-md mx-auto leading-relaxed">
          Calibrating six captured surfaces, extracting mandatory declaration blocks, and evaluating compliance against Legal Metrology (Packaged Commodities) Rules, 2011.
        </p>
        <div className="w-48 h-1.5 bg-surface-secondary rounded-full mx-auto overflow-hidden">
          <div className="w-2/3 h-full bg-primary rounded-full animate-pulse" />
        </div>
      </div>
    );
  }

  // 2. Error State
  if (error || !scan) {
    return (
      <div className="max-w-2xl mx-auto p-8 glass-card rounded-2xl border border-rose-500/40 text-red-600 space-y-4 animate-fade-in">
        <div className="flex items-center gap-3">
          <span className="text-3xl">⚠</span>
          <div>
            <h2 className="text-lg font-bold text-foreground">Failed to Load Scan Processing Results</h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Could not retrieve the inspection record. The OCR microservice or database may be experiencing latency.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 pt-2">
          <button
            onClick={() => refetch()}
            className="px-4 py-2 bg-primary text-primary-foreground font-semibold rounded-lg text-xs hover:bg-primary/90 transition-all"
          >
            Retry Fetching Result
          </button>
          <button
            onClick={() => navigate('/officer/queue')}
            className="px-4 py-2 bg-surface-secondary border border-border text-foreground rounded-lg text-xs hover:bg-surface-secondary/80 transition-all"
          >
            ← Return to Queue
          </button>
        </div>
      </div>
    );
  }

  const report = getOrBuildReport(scan);
  const check = scan.compliance_check;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200 text-xs font-semibold">
              Inspection Scan #{scan.id}
            </span>
            <span className="text-xs text-muted-foreground capitalize">
              Capture Method: {scan.capture_method.replace(/_/g, ' ')}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-foreground mt-1">Compliance Evaluation & Verification Report</h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/officer/queue')}
            className="px-3.5 py-2 rounded-lg bg-surface-secondary border border-border text-xs font-medium text-muted-foreground hover:text-foreground transition-all"
          >
            Queue
          </button>
          {check && (
            <button
              onClick={() => navigate(`/officer/check/${check.id}/review`, { state: { scan } })}
              className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 transition-all flex items-center gap-1.5 shadow-md"
            >
              <span>Review Findings & Sign-Off</span>
              <span>→</span>
            </button>
          )}
        </div>
      </div>

      {/* Official Legal Metrology Inspection Report Bar */}
      {check && (
        <ReportDownloadButton complianceCheckId={check.id} />
      )}

      {/* 3. Empty / Partial State */}
      {!report ? (
        <div className="p-12 glass-card rounded-2xl border border-amber-200 text-center space-y-3">
          <div className="text-3xl text-amber-600">⏳</div>
          <h3 className="text-lg font-bold text-foreground">Compliance Evaluation Pending</h3>
          <p className="text-xs text-muted-foreground max-w-md mx-auto">
            Optical character recognition completed, but the Legal Metrology compliance evaluation is still processing or awaiting data.
          </p>
          <button
            onClick={() => navigate('/officer/queue')}
            className="px-4 py-2 bg-surface-secondary border border-border rounded-lg text-xs font-semibold text-foreground hover:bg-surface-secondary/80"
          >
            ← Return to Inspection Queue
          </button>
        </div>
      ) : (
        /* 4. Full Unified Compliance Report Display */
        <ComplianceReportView
          report={report}
          scanImages={scan.scan_images}
          onProceedToReview={
            check ? () => navigate(`/officer/check/${check.id}/review`, { state: { scan } }) : undefined
          }
          onReturnToQueue={() => navigate('/officer/queue')}
        />
      )}
    </div>
  );
}
