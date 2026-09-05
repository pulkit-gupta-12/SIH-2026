import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchLatestReport,
  generateCaseReport,
  generateCheckReport,
  type ReportResult,
} from '../api';

interface ReportDownloadButtonProps {
  caseId?: number | string;
  complianceCheckId?: number | string;
  className?: string;
  compact?: boolean;
}

export default function ReportDownloadButton({
  caseId,
  complianceCheckId,
  className = '',
  compact = false,
}: ReportDownloadButtonProps) {
  const queryClient = useQueryClient();

  const queryKey = ['inspection-report', caseId || null, complianceCheckId || null];

  const { data: existingReport, isLoading: isCheckingReport } = useQuery<ReportResult | null>({
    queryKey,
    queryFn: () => fetchLatestReport({ caseId, checkId: complianceCheckId }),
    enabled: Boolean(caseId || complianceCheckId),
    staleTime: 30000,
  });

  const reportMutation = useMutation({
    mutationFn: (regenerate: boolean = false) => {
      if (caseId) {
        return generateCaseReport(caseId, regenerate);
      }
      if (complianceCheckId) {
        return generateCheckReport(complianceCheckId, regenerate);
      }
      throw new Error('Either caseId or complianceCheckId must be provided.');
    },
    onSuccess: (newReport) => {
      queryClient.setQueryData(queryKey, newReport);
    },
  });

  const handleGenerate = (regenerate: boolean) => {
    reportMutation.mutate(regenerate);
  };

  const isGenerating = reportMutation.isPending;
  const report = existingReport || reportMutation.data;

  // Render when a report is available
  if (report && report.file_url) {
    if (compact) {
      return (
        <div className={`inline-flex items-center gap-2 ${className}`}>
          <a
            href={report.file_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold shadow-sm transition-all"
            title={`Generated: ${new Date(report.generated_at).toLocaleString()}`}
          >
            <span>📄</span>
            <span>Download PDF ({report.report_code || `ID #${report.id}`})</span>
          </a>
          <button
            onClick={() => handleGenerate(true)}
            disabled={isGenerating}
            className="p-1.5 text-xs text-muted-foreground hover:text-foreground bg-surface-secondary border border-border/70 rounded-lg transition-all"
            title="Regenerate Report"
          >
            {isGenerating ? '⏳' : '🔄'}
          </button>
        </div>
      );
    }

    return (
      <div className={`p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/5 space-y-3 ${className}`}>
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-600/10 border border-emerald-500/30 text-emerald-600 flex items-center justify-center text-xl">
              📄
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-foreground">
                  Legal Metrology Inspection Report
                </span>
                <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-600 border border-emerald-500/30 text-[10px] font-mono font-bold">
                  {report.report_code || `LMR-${report.id}`}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Generated {new Date(report.generated_at).toLocaleDateString()} at{' '}
                {new Date(report.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • Official Statutory Record
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <a
              href={report.file_url}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs transition-all shadow-md flex items-center gap-2"
            >
              <span>⬇</span>
              <span>Download PDF</span>
            </a>

            <button
              onClick={() => handleGenerate(true)}
              disabled={isGenerating}
              className="px-3 py-2 rounded-lg bg-surface-secondary border border-border text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-surface-secondary/80 transition-all flex items-center gap-1.5"
              title="Generate a fresh copy of the statutory report"
            >
              <span>{isGenerating ? '⏳' : '🔄'}</span>
              <span>{isGenerating ? 'Regenerating...' : 'Regenerate'}</span>
            </button>
          </div>
        </div>

        {reportMutation.isError && (
          <p className="text-xs text-rose-500">
            Regeneration failed: {(reportMutation.error as Error)?.message || 'Internal server error.'}
          </p>
        )}
      </div>
    );
  }

  // Render when no report has been generated yet
  return (
    <div className={`inline-flex flex-col items-start gap-1.5 ${className}`}>
      <button
        onClick={() => handleGenerate(false)}
        disabled={isGenerating || isCheckingReport}
        className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-all shadow-md flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span>{isGenerating ? '⚙️' : '📋'}</span>
        <span>{isGenerating ? 'Generating Inspection PDF...' : 'Generate Inspection Report'}</span>
      </button>

      {reportMutation.isError && (
        <span className="text-xs text-rose-500">
          {(reportMutation.error as Error)?.message || 'Generation failed.'}
        </span>
      )}
    </div>
  );
}
