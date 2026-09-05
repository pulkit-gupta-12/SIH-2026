import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  fetchInspectionHistory,
  generateCheckReport,
  type InspectionHistoryItem,
} from '../api';
import StatusPill from '../../../components/ui/StatusPill';

export default function InspectionHistoryView() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState<string>('');
  const [verdictFilter, setVerdictFilter] = useState<string>('all');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const [generatingId, setGeneratingId] = useState<number | null>(null);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['inspection-history', searchTerm, verdictFilter, dateFrom, dateTo],
    queryFn: () =>
      fetchInspectionHistory({
        search: searchTerm,
        verdict: verdictFilter,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      }),
  });

  const generateReportMutation = useMutation({
    mutationFn: async (checkId: number) => {
      setGeneratingId(checkId);
      return generateCheckReport(checkId, true);
    },
    onSuccess: (reportData) => {
      queryClient.invalidateQueries({ queryKey: ['inspection-history'] });
      if (reportData?.file_url) {
        window.open(reportData.file_url, '_blank');
      }
    },
    onError: (err) => {
      console.error('Failed to generate report:', err);
    },
    onSettled: () => {
      setGeneratingId(null);
    },
  });

  const historyItems: InspectionHistoryItem[] = data?.results ?? [];

  const handleClearFilters = () => {
    setSearchTerm('');
    setVerdictFilter('all');
    setDateFrom('');
    setDateTo('');
  };

  const hasActiveFilters = Boolean(searchTerm || (verdictFilter && verdictFilter !== 'all') || dateFrom || dateTo);

  return (
    <div className="space-y-4">
      {/* Search & Filter Controls Bar */}
      <div className="glass-card p-4 rounded-xl space-y-3">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          {/* Search Input */}
          <div className="md:col-span-2 relative">
            <input
              type="text"
              placeholder="Search by brand, product name, or GTIN barcode..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-3.5 py-2 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
            />
          </div>

          {/* Verdict Filter */}
          <div>
            <select
              value={verdictFilter}
              onChange={(e) => setVerdictFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors"
            >
              <option value="all">All Verdicts</option>
              <option value="compliant">Compliant</option>
              <option value="non_compliant">Non-Compliant</option>
              <option value="needs_review">Needs Review</option>
            </select>
          </div>

          {/* Clear Filters Button */}
          <div className="flex items-center justify-end">
            {hasActiveFilters && (
              <button
                type="button"
                onClick={handleClearFilters}
                className="w-full md:w-auto px-3 py-2 text-xs font-medium rounded-lg text-[var(--color-accent)] hover:bg-[var(--color-accent-subtle)] border border-[var(--color-accent-muted)] transition-colors flex items-center justify-center gap-1.5"
              >
                <span>✕</span>
                <span>Reset Filters</span>
              </button>
            )}
          </div>
        </div>

        {/* Date Range Sub-row */}
        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-[var(--color-border)] text-xs text-[var(--color-text-secondary)]">
          <span className="font-medium text-[var(--color-text-primary)] flex items-center gap-1">
            <span>📅</span>
            <span>Date Range:</span>
          </span>
          <div className="flex items-center gap-2">
            <label className="text-[var(--color-text-muted)]">From:</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-2 py-1 rounded bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]"
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-[var(--color-text-muted)]">To:</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-2 py-1 rounded bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-primary)] focus:outline-none focus:border-[var(--color-accent)]"
            />
          </div>
          <span className="ml-auto text-[var(--color-text-muted)] text-[11px]">
            Showing {historyItems.length} inspection{historyItems.length === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <div className="p-12 text-center text-[var(--color-text-muted)] glass-card rounded-xl">
          <div className="animate-spin text-3xl mb-3">⚙️</div>
          <p className="text-sm font-medium">Loading completed inspection history...</p>
        </div>
      ) : error ? (
        <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-700 flex items-center justify-between">
          <p className="text-sm">Failed to load inspection history records.</p>
          <button
            onClick={() => refetch()}
            className="px-3 py-1 bg-red-100 hover:bg-red-200 rounded-lg text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      ) : historyItems.length === 0 ? (
        <div className="p-12 text-center text-[var(--color-text-muted)] glass-card rounded-xl space-y-2">
          <div className="text-3xl">📂</div>
          <p className="text-base font-semibold text-[var(--color-text-primary)]">
            No completed inspections found
          </p>
          <p className="text-xs max-w-md mx-auto">
            {hasActiveFilters
              ? 'No inspections matched your filter criteria. Try adjusting or resetting your search filters above.'
              : 'Inspections completed by field officers will appear here with automated statutory findings and official reports.'}
          </p>
          {hasActiveFilters && (
            <button
              onClick={handleClearFilters}
              className="mt-3 px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--color-accent)] bg-[var(--color-accent-subtle)] hover:bg-[var(--color-accent-muted)] transition-colors"
            >
              Clear all filters
            </button>
          )}
        </div>
      ) : (
        <>
          {/* Desktop Table View */}
          <div className="hidden lg:block glass-card rounded-xl overflow-hidden border border-[var(--color-border)]">
            <table className="w-full text-left text-xs">
              <thead className="bg-[var(--color-surface-tertiary)] border-b border-[var(--color-border)] text-[var(--color-text-muted)] uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-4">Product / Identification</th>
                  <th className="py-3 px-3">Inspection Date</th>
                  <th className="py-3 px-3">Inspector</th>
                  <th className="py-3 px-3">Verdict & Confidence</th>
                  <th className="py-3 px-3">Findings & Violations</th>
                  <th className="py-3 px-4 text-right">Statutory Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--color-border)] text-[var(--color-text-primary)]">
                {historyItems.map((item) => {
                  const isGen = generatingId === item.compliance_check_id;
                  const dateObj = new Date(item.inspection_date);
                  const formattedDate = dateObj.toLocaleDateString(undefined, {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  });
                  const formattedTime = dateObj.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  });

                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-[var(--color-surface-tertiary)]/50 transition-colors"
                    >
                      {/* Product identity */}
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-sm text-[var(--color-text-primary)]">
                          {item.product.brand_name} — {item.product.product_name}
                        </div>
                        <div className="flex items-center gap-2 mt-1 text-[11px] text-[var(--color-text-muted)]">
                          <span className="font-mono bg-[var(--color-surface-tertiary)] px-1.5 py-0.5 rounded border border-[var(--color-border)]">
                            {item.product.gtin_barcode}
                          </span>
                          <span className="capitalize">{item.product.category}</span>
                        </div>
                      </td>

                      {/* Inspection date */}
                      <td className="py-3.5 px-3 whitespace-nowrap">
                        <div className="font-medium text-[var(--color-text-primary)]">{formattedDate}</div>
                        <div className="text-[11px] text-[var(--color-text-muted)]">{formattedTime}</div>
                      </td>

                      {/* Inspector */}
                      <td className="py-3.5 px-3">
                        <div className="font-medium text-[var(--color-text-primary)]">{item.officer.name}</div>
                        <div className="text-[11px] text-[var(--color-text-muted)] font-mono">
                          @{item.officer.username}
                        </div>
                      </td>

                      {/* Verdict */}
                      <td className="py-3.5 px-3 whitespace-nowrap">
                        <div className="flex flex-col gap-1 items-start">
                          <StatusPill verdict={item.verdict} />
                          <span className="text-[11px] text-[var(--color-text-muted)] font-mono">
                            {(item.overall_confidence * 100).toFixed(0)}% OCR Conf.
                          </span>
                        </div>
                      </td>

                      {/* Violations */}
                      <td className="py-3.5 px-3 max-w-xs">
                        {item.violations_count > 0 ? (
                          <div className="space-y-1">
                            <span className="inline-flex items-center gap-1 text-xs font-semibold text-red-600 bg-red-50 border border-red-200 px-2 py-0.5 rounded">
                              <span>⚠️</span>
                              <span>{item.violations_count} Violation{item.violations_count === 1 ? '' : 's'}</span>
                            </span>
                            {item.violations[0] && (
                              <p className="text-[11px] text-[var(--color-text-muted)] truncate" title={item.violations[0].description}>
                                {item.violations[0].description}
                              </p>
                            )}
                          </div>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 border border-green-200 px-2 py-0.5 rounded">
                            <span>✓</span>
                            <span>Compliant</span>
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => navigate(`/officer/check/${item.compliance_check_id}/review`)}
                            className="px-2.5 py-1.5 rounded-lg border border-[var(--color-border)] hover:bg-[var(--color-surface-tertiary)] text-xs font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors"
                            title="View full audit findings and field extraction breakdown"
                          >
                            Findings
                          </button>

                          {item.report?.file_url ? (
                            <a
                              href={item.report.file_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white transition-all shadow-sm flex items-center gap-1"
                              style={{ background: 'var(--color-accent)' }}
                              title="Download official statutory inspection PDF report"
                            >
                              <span>📄</span>
                              <span>Report</span>
                            </a>
                          ) : (
                            <button
                              type="button"
                              onClick={() => generateReportMutation.mutate(item.compliance_check_id)}
                              disabled={isGen}
                              className="px-3 py-1.5 rounded-lg text-xs font-semibold text-[var(--color-accent)] bg-[var(--color-accent-subtle)] hover:bg-[var(--color-accent-muted)] border border-[var(--color-accent-muted)] transition-colors flex items-center gap-1"
                              title="Generate official statutory inspection PDF report"
                            >
                              {isGen ? (
                                <>
                                  <span className="animate-spin text-xs">⚙️</span>
                                  <span>Building...</span>
                                </>
                              ) : (
                                <>
                                  <span>📝</span>
                                  <span>Generate</span>
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Mobile Stacked Card View */}
          <div className="block lg:hidden space-y-3">
            {historyItems.map((item) => {
              const isGen = generatingId === item.compliance_check_id;
              const dateObj = new Date(item.inspection_date);
              const formattedDate = dateObj.toLocaleDateString(undefined, {
                day: 'numeric',
                month: 'short',
                year: 'numeric',
              });

              return (
                <div
                  key={item.id}
                  className="p-4 rounded-xl glass-card border border-[var(--color-border)] space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h4 className="text-sm font-bold text-[var(--color-text-primary)]">
                        {item.product.brand_name} — {item.product.product_name}
                      </h4>
                      <p className="text-xs text-[var(--color-text-muted)] font-mono mt-0.5">
                        GTIN: {item.product.gtin_barcode}
                      </p>
                    </div>
                    <StatusPill verdict={item.verdict} />
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs py-2 border-y border-[var(--color-border)] text-[var(--color-text-secondary)]">
                    <div>
                      <span className="text-[var(--color-text-muted)] block text-[10px] uppercase">Inspection Date</span>
                      <span className="font-medium text-[var(--color-text-primary)]">{formattedDate}</span>
                    </div>
                    <div>
                      <span className="text-[var(--color-text-muted)] block text-[10px] uppercase">Inspecting Officer</span>
                      <span className="font-medium text-[var(--color-text-primary)]">{item.officer.name}</span>
                    </div>
                  </div>

                  {item.violations_count > 0 && item.violations[0] && (
                    <div className="text-xs p-2 bg-red-50/70 border border-red-200 rounded text-red-700">
                      <span className="font-semibold">⚠️ {item.violations_count} Violation(s): </span>
                      <span>{item.violations[0].description}</span>
                    </div>
                  )}

                  <div className="flex items-center justify-between gap-2 pt-1">
                    <button
                      type="button"
                      onClick={() => navigate(`/officer/check/${item.compliance_check_id}/review`)}
                      className="px-3 py-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface-tertiary)] text-xs font-medium text-[var(--color-text-secondary)]"
                    >
                      Review Findings
                    </button>

                    {item.report?.file_url ? (
                      <a
                        href={item.report.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold text-white shadow-sm flex items-center gap-1"
                        style={{ background: 'var(--color-accent)' }}
                      >
                        <span>📄</span>
                        <span>Download PDF</span>
                      </a>
                    ) : (
                      <button
                        type="button"
                        onClick={() => generateReportMutation.mutate(item.compliance_check_id)}
                        disabled={isGen}
                        className="px-3 py-1.5 rounded-lg text-xs font-semibold text-[var(--color-accent)] bg-[var(--color-accent-subtle)] border border-[var(--color-accent-muted)]"
                      >
                        {isGen ? 'Building PDF...' : 'Generate PDF'}
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}
