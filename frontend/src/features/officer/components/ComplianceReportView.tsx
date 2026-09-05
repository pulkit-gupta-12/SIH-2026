import { useState } from 'react';
import type { ComplianceReport } from '../api';
import RuleFindingCard from './RuleFindingCard';

interface ComplianceReportViewProps {
  report: ComplianceReport;
  scanImages?: Array<{ id: number; image_url: string; angle?: string; angle_type?: string }>;
  onProceedToReview?: () => void;
  onReturnToQueue?: () => void;
}

type TabKey = 'all' | 'violations' | 'warnings' | 'reviews' | 'passed' | 'evidence';

export default function ComplianceReportView({
  report,
  scanImages = [],
  onProceedToReview,
  onReturnToQueue,
}: ComplianceReportViewProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('all');
  const [selectedPanelImage, setSelectedPanelImage] = useState<string | null>(null);
  const [expandAllPassed, setExpandAllPassed] = useState(false);

  const status = report.overall_status;
  const isNonCompliant = status === 'NON_COMPLIANT';
  const isNeedsReview = status === 'NEEDS_REVIEW';

  const summary = report.summary || {
    total_rules: 0,
    passed: 0,
    failed: 0,
    warnings: 0,
    review_required: 0,
    not_applicable: 0,
  };

  const violations = report.violations || [];
  const warnings = report.warnings || [];
  const reviews = report.reviews || [];
  const passedRules = report.passed_rules || [];
  const evidenceList = report.evidence || [];

  // Helper to open capture image for a panel
  const handleViewImage = (panelName: string) => {
    if (!scanImages || scanImages.length === 0) return;

    // Match image by angle or angle_type
    const found = scanImages.find(
      (img) =>
        (img.angle_type && img.angle_type.toLowerCase().includes(panelName.toLowerCase())) ||
        (img.angle && img.angle.toLowerCase().includes(panelName.toLowerCase()))
    );

    if (found) {
      setSelectedPanelImage(found.image_url);
    } else if (scanImages[0]) {
      setSelectedPanelImage(scanImages[0].image_url);
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Overall Status Banner */}
      <div
        className={`p-6 rounded-2xl border transition-all ${
          isNonCompliant
            ? 'bg-rose-500/10 border-rose-500/40 text-rose-200 shadow-lg shadow-rose-950/20'
            : isNeedsReview
            ? 'bg-amber-500/10 border-amber-500/40 text-amber-200 shadow-lg shadow-amber-950/20'
            : 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200 shadow-lg shadow-emerald-950/20'
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border shadow-sm ${
                  isNonCompliant
                    ? 'bg-rose-500/20 text-rose-300 border-rose-500/50'
                    : isNeedsReview
                    ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                    : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50'
                }`}
              >
                {isNonCompliant ? '✕ NON-COMPLIANT' : isNeedsReview ? '⚠ NEEDS REVIEW' : '✓ COMPLIANT'}
              </span>

              <span className="text-xs font-mono bg-surface-secondary/70 px-2.5 py-0.5 rounded border border-border/50 text-muted-foreground">
                Inspection ID: {report.inspection_id}
              </span>

              <span className="text-xs text-muted-foreground">
                Generated: {new Date(report.generated_at).toLocaleString()}
              </span>
            </div>

            <h2 className="text-2xl font-bold text-foreground">
              {isNonCompliant
                ? `Flagged ${summary.failed} Regulatory Non-Compliance Finding(s)`
                : isNeedsReview
                ? `${summary.review_required} Check(s) Require Officer Verification`
                : 'All Package Declarations Meet Statutory Standards'}
            </h2>

            <p className="text-xs text-muted-foreground max-w-3xl leading-relaxed">
              {isNonCompliant
                ? 'Deterministic and semantic rules have detected non-compliance against Legal Metrology (Packaged Commodities) Rules, 2011. Review findings below before issuing an improvement notice or seizure.'
                : isNeedsReview
                ? 'One or more mandatory statements contain ambiguous OCR, low sensor confidence, or unverified declarations. Officer physical confirmation is required before final sign-off.'
                : 'All evaluated mandatory declarations (MRP format, net quantity, manufacturing dates, complete address, and generic commodity name) strictly conform to statutory guidelines.'}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 self-start md:self-center">
            {onReturnToQueue && (
              <button
                onClick={onReturnToQueue}
                className="px-3.5 py-2 rounded-lg bg-surface-secondary border border-border text-xs font-medium text-muted-foreground hover:text-foreground transition-all"
              >
                Inspection Queue
              </button>
            )}
            {onProceedToReview && (
              <button
                onClick={onProceedToReview}
                className="px-4 py-2 rounded-lg bg-primary text-primary-foreground font-semibold text-xs hover:bg-primary/90 transition-all flex items-center gap-1.5 shadow-md"
              >
                <span>Officer Review & Sign-Off</span>
                <span>→</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 2. Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {/* Passed */}
        <button
          onClick={() => setActiveTab('passed')}
          className={`p-4 rounded-xl glass-card border text-left transition-all hover:scale-[1.02] ${
            activeTab === 'passed' ? 'border-emerald-500 ring-1 ring-emerald-500/50' : 'border-border/60'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Passed Checks</span>
            <span className="text-emerald-400 font-bold">✓</span>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-emerald-400">{summary.passed}</div>
          <p className="text-[11px] text-muted-foreground mt-0.5">Statutory rules verified</p>
        </button>

        {/* Violations */}
        <button
          onClick={() => setActiveTab('violations')}
          className={`p-4 rounded-xl glass-card border text-left transition-all hover:scale-[1.02] ${
            activeTab === 'violations' ? 'border-rose-500 ring-1 ring-rose-500/50' : 'border-border/60'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Violations</span>
            <span className="text-rose-400 font-bold">✕</span>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-rose-400">{summary.failed}</div>
          <p className="text-[11px] text-muted-foreground mt-0.5">Regulatory breaches</p>
        </button>

        {/* Warnings */}
        <button
          onClick={() => setActiveTab('warnings')}
          className={`p-4 rounded-xl glass-card border text-left transition-all hover:scale-[1.02] ${
            activeTab === 'warnings' ? 'border-orange-500 ring-1 ring-orange-500/50' : 'border-border/60'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Warnings</span>
            <span className="text-orange-400 font-bold">!</span>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-orange-400">{summary.warnings}</div>
          <p className="text-[11px] text-muted-foreground mt-0.5">Advisories & notices</p>
        </button>

        {/* Needs Review */}
        <button
          onClick={() => setActiveTab('reviews')}
          className={`p-4 rounded-xl glass-card border text-left transition-all hover:scale-[1.02] ${
            activeTab === 'reviews' ? 'border-amber-500 ring-1 ring-amber-500/50' : 'border-border/60'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Needs Review</span>
            <span className="text-amber-400 font-bold">⚠</span>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-amber-400">{summary.review_required}</div>
          <p className="text-[11px] text-muted-foreground mt-0.5">OCR/human validation</p>
        </button>

        {/* Not Applicable */}
        <button
          onClick={() => setActiveTab('all')}
          className={`p-4 rounded-xl glass-card border text-left transition-all hover:scale-[1.02] ${
            activeTab === 'all' ? 'border-slate-400 ring-1 ring-slate-400/50' : 'border-border/60'
          }`}
        >
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Total Evaluated</span>
            <span className="text-slate-400 font-bold">#</span>
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-foreground">{summary.total_rules}</div>
          <p className="text-[11px] text-muted-foreground mt-0.5">{summary.not_applicable} not applicable</p>
        </button>
      </div>

      {/* 3. Section Navigation Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border/50 pb-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'all'
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'bg-surface-secondary/60 text-muted-foreground hover:text-foreground'
            }`}
          >
            All Findings ({violations.length + warnings.length + reviews.length + passedRules.length})
          </button>

          <button
            onClick={() => setActiveTab('violations')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'violations'
                ? 'bg-rose-500 text-white shadow-sm'
                : 'bg-surface-secondary/60 text-rose-300 hover:text-rose-200'
            }`}
          >
            Violations ({violations.length})
          </button>

          <button
            onClick={() => setActiveTab('warnings')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'warnings'
                ? 'bg-orange-500 text-white shadow-sm'
                : 'bg-surface-secondary/60 text-orange-300 hover:text-orange-200'
            }`}
          >
            Warnings ({warnings.length})
          </button>

          <button
            onClick={() => setActiveTab('reviews')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'reviews'
                ? 'bg-amber-500 text-slate-950 font-bold shadow-sm'
                : 'bg-surface-secondary/60 text-amber-300 hover:text-amber-200'
            }`}
          >
            Needs Review ({reviews.length})
          </button>

          <button
            onClick={() => setActiveTab('passed')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'passed'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-surface-secondary/60 text-emerald-300 hover:text-emerald-200'
            }`}
          >
            Passed Checks ({passedRules.length})
          </button>

          <button
            onClick={() => setActiveTab('evidence')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === 'evidence'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-surface-secondary/60 text-blue-300 hover:text-blue-200'
            }`}
          >
            OCR Raw Evidence ({evidenceList.length})
          </button>
        </div>

        {activeTab === 'passed' && (
          <button
            onClick={() => setExpandAllPassed(!expandAllPassed)}
            className="px-2.5 py-1 rounded bg-surface-secondary border border-border text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            {expandAllPassed ? 'Collapse All' : 'Expand All'}
          </button>
        )}
      </div>

      {/* 4. Tab Content Panels */}
      <div className="space-y-4">
        {/* Violations View */}
        {(activeTab === 'all' || activeTab === 'violations') && violations.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-rose-400 flex items-center gap-2">
                <span>✕</span>
                <span>Confirmed & Potential Non-Compliance Issues ({violations.length})</span>
              </h3>
              <span className="text-[11px] text-muted-foreground font-mono">Status: FAIL</span>
            </div>
            <div className="space-y-3">
              {violations.map((finding) => (
                <RuleFindingCard
                  key={finding.rule_id}
                  finding={finding}
                  defaultExpanded={true}
                  onViewImage={handleViewImage}
                />
              ))}
            </div>
          </div>
        )}

        {/* Warnings View */}
        {(activeTab === 'all' || activeTab === 'warnings') && warnings.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-orange-400 flex items-center gap-2">
                <span>!</span>
                <span>Statutory Advisories & Warnings ({warnings.length})</span>
              </h3>
              <span className="text-[11px] text-muted-foreground font-mono">Status: WARNING</span>
            </div>
            <div className="space-y-3">
              {warnings.map((finding) => (
                <RuleFindingCard
                  key={finding.rule_id}
                  finding={finding}
                  defaultExpanded={true}
                  onViewImage={handleViewImage}
                />
              ))}
            </div>
          </div>
        )}

        {/* Needs Review View */}
        {(activeTab === 'all' || activeTab === 'reviews') && reviews.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-amber-400 flex items-center gap-2">
                <span>⚠</span>
                <span>Human Review & Verification Required ({reviews.length})</span>
              </h3>
              <span className="text-[11px] text-muted-foreground font-mono">Status: REVIEW</span>
            </div>
            <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 leading-relaxed">
              <strong>Notice for Officer:</strong> The following checks could not be deterministically confirmed due to
              OCR uncertainty, blurry surface, or semantic ambiguity. Please examine the evidence before making a legal determination.
            </div>
            <div className="space-y-3">
              {reviews.map((finding) => (
                <RuleFindingCard
                  key={finding.rule_id}
                  finding={finding}
                  defaultExpanded={true}
                  onViewImage={handleViewImage}
                />
              ))}
            </div>
          </div>
        )}

        {/* Passed Checks View */}
        {(activeTab === 'all' || activeTab === 'passed') && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-emerald-400 flex items-center gap-2">
                <span>✓</span>
                <span>Statutory Checks Passing Standards ({passedRules.length})</span>
              </h3>
              <span className="text-[11px] text-muted-foreground font-mono">Status: PASS</span>
            </div>
            {passedRules.length === 0 ? (
              <p className="text-xs text-muted-foreground p-4 text-center glass-card rounded-xl">
                No passed checks recorded for this scan.
              </p>
            ) : (
              <div className="space-y-3">
                {passedRules.map((finding) => (
                  <RuleFindingCard
                    key={finding.rule_id}
                    finding={finding}
                    defaultExpanded={expandAllPassed}
                    onViewImage={handleViewImage}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Raw Evidence Inspector */}
        {(activeTab === 'all' || activeTab === 'evidence') && (
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                <span>🔍</span>
                <span>Complete OCR & Package Evidence Log ({evidenceList.length})</span>
              </h3>
              <span className="text-[11px] text-muted-foreground font-mono">Never Discarded</span>
            </div>

            <div className="rounded-xl glass-card border border-border/60 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-surface-secondary text-muted-foreground font-semibold border-b border-border/50">
                    <tr>
                      <th className="p-3">Field</th>
                      <th className="p-3">Raw Extracted OCR Text</th>
                      <th className="p-3">Source Panel</th>
                      <th className="p-3">Confidence</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40 font-mono">
                    {evidenceList.map((ev, idx) => (
                      <tr key={`${ev.field}-${idx}`} className="hover:bg-muted/20">
                        <td className="p-3 font-semibold text-foreground capitalize font-sans">
                          {ev.field.replace(/_/g, ' ')}
                        </td>
                        <td className="p-3 text-foreground/90 font-sans max-w-xs truncate">
                          {ev.raw_text ? `"${ev.raw_text}"` : '—'}
                        </td>
                        <td className="p-3 text-muted-foreground capitalize">
                          {ev.source_panel.replace(/_/g, ' ')}
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                              ev.confidence >= 0.9
                                ? 'bg-emerald-500/20 text-emerald-300'
                                : ev.confidence >= 0.6
                                ? 'bg-amber-500/20 text-amber-300'
                                : 'bg-rose-500/20 text-rose-300'
                            }`}
                          >
                            {Math.round(ev.confidence * 100)}%
                          </span>
                        </td>
                        <td className="p-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${
                              ev.normalization_status === 'success'
                                ? 'text-emerald-300 bg-emerald-500/10'
                                : ev.normalization_status === 'raw'
                                ? 'text-blue-300 bg-blue-500/10'
                                : 'text-amber-300 bg-amber-500/10'
                            }`}
                          >
                            {ev.normalization_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Capture Panel Preview Modal */}
      {selectedPanelImage && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
          onClick={() => setSelectedPanelImage(null)}
        >
          <div
            className="max-w-2xl w-full p-4 rounded-2xl glass-card border border-border space-y-3 bg-surface-primary"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-foreground">Original Capture Panel Verification</h4>
              <button
                onClick={() => setSelectedPanelImage(null)}
                className="text-muted-foreground hover:text-foreground text-sm font-bold p-1"
              >
                ✕ Close
              </button>
            </div>
            <div className="rounded-xl overflow-hidden border border-border/50 max-h-[60vh] flex items-center justify-center bg-black">
              <img
                src={selectedPanelImage}
                alt="Source Panel Capture"
                className="object-contain max-h-[60vh] w-full"
              />
            </div>
            <p className="text-[11px] text-muted-foreground text-center">
              Original captured frame used for optical character recognition and legal calibration.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
