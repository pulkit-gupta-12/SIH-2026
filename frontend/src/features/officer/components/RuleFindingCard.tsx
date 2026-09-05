import { useState } from 'react';
import type { RuleFinding } from '../api';

interface RuleFindingCardProps {
  finding: RuleFinding;
  defaultExpanded?: boolean;
  onViewImage?: (panelName: string) => void;
}

export default function RuleFindingCard({
  finding,
  defaultExpanded = false,
  onViewImage,
}: RuleFindingCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [showEvidence, setShowEvidence] = useState(false);

  const status = finding.status;
  const isFail = status === 'FAIL';
  const isReview = status === 'REVIEW';
  const isWarning = status === 'WARNING';
  const isPass = status === 'PASS';

  // Determine border & background accents
  let cardBorder = 'border-border/60';
  let badgeColor = 'bg-gray-50 text-[var(--color-text-secondary)] border-gray-200';
  let statusText = 'Not Applicable';

  if (isFail) {
    cardBorder = 'border-rose-500/40 bg-rose-950/10 hover:border-rose-500/70';
    badgeColor = 'bg-red-50 text-red-600 border-rose-500/40';
    statusText = 'Potential Non-Compliance Detected';
  } else if (isReview) {
    cardBorder = 'border-amber-500/40 bg-amber-950/10 hover:border-amber-500/70';
    badgeColor = 'bg-amber-50 text-amber-600 border-amber-500/40';
    statusText = finding.reason.toLowerCase().includes('ocr') || finding.reason.toLowerCase().includes('confidence')
      ? 'OCR Uncertainty — Review Required'
      : 'Officer Verification Required';
  } else if (isWarning) {
    cardBorder = 'border-orange-500/40 bg-orange-950/10 hover:border-orange-500/70';
    badgeColor = 'bg-orange-500/20 text-orange-300 border-orange-500/40';
    statusText = 'Statutory Advisory / Warning';
  } else if (isPass) {
    cardBorder = 'border-green-200 bg-green-50 hover:border-green-300';
    badgeColor = 'bg-[var(--color-accent)]/15 text-[var(--color-accent)] border-green-200';
    statusText = 'Statutory Requirement Verified';
  }

  // Severity styling
  const severityStyles: Record<string, string> = {
    CRITICAL: 'bg-red-500/20 text-red-300 border-red-500/40',
    HIGH: 'bg-red-50 text-red-600 border-rose-500/40',
    MEDIUM: 'bg-amber-50 text-amber-600 border-amber-500/40',
    LOW: 'bg-blue-50 text-blue-600 border-blue-500/40',
  };

  const panelLabels: Record<string, string> = {
    front_pdp: 'Front PDP (Panel 1)',
    mandatory_declaration: 'Declaration Panel (Panel 2)',
    mrp: 'MRP Close-up (Panel 3)',
    manufacturer_address: 'Manufacturer Block (Panel 4)',
    barcode: 'Barcode / EAN (Panel 5)',
    seal: 'Wrap-Around / Seal (Panel 6)',
    all_panels: 'All Panels OCR',
    unspecified: 'Capture Surface',
  };

  const humanPanel = panelLabels[finding.source_panel] || finding.source_panel.replace(/_/g, ' ');

  return (
    <div className={`p-4 rounded-xl glass-card border transition-all space-y-3 ${cardBorder}`}>
      {/* Header: Rule Code, Status Badge, Severity & Expand Button */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs font-bold text-foreground bg-surface-secondary px-2.5 py-1 rounded border border-border">
            {finding.rule_id}
          </span>
          <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${badgeColor}`}>
            {statusText}
          </span>
          <span
            className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${
              severityStyles[finding.severity] || severityStyles.MEDIUM
            }`}
          >
            {finding.severity}
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="font-mono text-[11px] bg-surface-secondary/70 px-2 py-0.5 rounded border border-border/40">
            Confidence: {Math.round(finding.confidence * 100)}%
          </span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="px-2 py-1 rounded hover:bg-surface-secondary text-foreground text-xs font-medium transition-colors"
            aria-label={isExpanded ? 'Collapse check details' : 'Expand check details'}
          >
            {isExpanded ? '▲ Hide Details' : '▼ View Details'}
          </button>
        </div>
      </div>

      {/* Main Title & Section Ref */}
      <div>
        <h4 className="text-sm font-semibold text-foreground">{finding.title}</h4>
        <p className="text-xs text-muted-foreground mt-0.5">{finding.section_ref}</p>
      </div>

      {/* Rationale / Explanatory Reason */}
      <div
        className={`p-3 rounded-lg text-xs leading-relaxed ${
          isFail
            ? 'bg-red-50 text-rose-800 border border-rose-200'
            : isReview
            ? 'bg-amber-50 text-amber-800 border border-amber-200'
            : isWarning
            ? 'bg-orange-50 text-orange-800 border border-orange-200'
            : 'bg-green-50 text-green-800 border border-green-200'
        }`}
      >
        <span className="font-semibold block mb-0.5">Evaluation Analysis:</span>
        {finding.reason}
      </div>

      {/* Expandable Details Section */}
      {isExpanded && (
        <div className="pt-2 border-t border-border/40 space-y-3 animate-fade-in text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Requirement */}
            <div className="p-3 rounded-lg bg-surface-secondary/50 border border-border/40">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                Statutory Requirement
              </span>
              <p className="text-foreground font-sans leading-relaxed">{finding.expected}</p>
            </div>

            {/* Detected Information */}
            <div className="p-3 rounded-lg bg-surface-secondary/50 border border-border/40">
              <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1">
                Detected Information
              </span>
              <p className="text-foreground font-mono font-medium">{finding.detected_value || 'Not Detected'}</p>
            </div>
          </div>

          {/* Context Footer: Source Capture, Verification Source & Evidence Toggle */}
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1 text-[11px] text-muted-foreground">
            <div className="flex items-center gap-3">
              <span>
                <strong className="text-foreground/80">Source Capture:</strong>{' '}
                <span className="capitalize">{humanPanel}</span>
              </span>
              {onViewImage && (
                <button
                  onClick={() => onViewImage(finding.source_panel)}
                  className="text-primary hover:underline text-[11px] font-medium"
                >
                  View Capture Panel ↗
                </button>
              )}
            </div>

            <div className="flex items-center gap-3">
              <span className="opacity-80">
                Evaluation: {finding.evaluation_source === 'semantic_llm' ? 'Semantic LLM' : 'Deterministic Engine'}
              </span>
              {finding.evidence && (
                <button
                  onClick={() => setShowEvidence(!showEvidence)}
                  className="px-2.5 py-1 rounded bg-card border border-border text-foreground font-medium hover:bg-card/80 transition-colors"
                >
                  {showEvidence ? 'Hide Raw Evidence' : 'View Raw Evidence'}
                </button>
              )}
            </div>
          </div>

          {/* Raw OCR Evidence Drawer */}
          {showEvidence && finding.evidence && (
            <div className="p-3 rounded-lg bg-[var(--color-surface-primary)]/70 border border-border/70 font-mono text-xs space-y-1.5 animate-slide-up">
              <div className="flex items-center justify-between text-[11px] text-muted-foreground pb-1 border-b border-border/30">
                <span>Raw OCR Extracted Snippet</span>
                {finding.evidence.bounding_box && (
                  <span>
                    BBox: [{finding.evidence.bounding_box.join(', ')}]
                  </span>
                )}
              </div>
              <p className="text-[var(--color-accent)] whitespace-pre-wrap break-words">
                {finding.evidence.raw_text ? `"${finding.evidence.raw_text}"` : 'No raw text snippet captured.'}
              </p>
              {finding.evidence.normalized_value && (
                <div className="pt-1 text-[11px] text-[var(--color-text-muted)]">
                  <span className="text-muted-foreground font-sans">Normalized: </span>
                  {typeof finding.evidence.normalized_value === 'object'
                    ? JSON.stringify(finding.evidence.normalized_value)
                    : String(finding.evidence.normalized_value)}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
