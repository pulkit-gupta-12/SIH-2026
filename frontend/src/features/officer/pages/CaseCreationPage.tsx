import { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  createEnforcementCase,
  fetchProductViolationHistory,
  fetchOfficerCases,
  type EnforcementCaseResult,
  type ProductViolationTimeline,
} from '../api';
import apiClient from '../../../services/apiClient';

interface ProductSummary {
  id: number;
  gtin_barcode: string;
  brand_name: string;
  product_name: string;
  category: string;
  manufacturer_name: string;
  manufacturer_address: string;
}

export default function CaseCreationPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const prefilledProduct = searchParams.get('product');
  const prefilledViolation = searchParams.get('violation');
  const prefilledComplaint = searchParams.get('complaint');

  const [productId, setProductId] = useState<string>(prefilledProduct || '');
  const [violationId, setViolationId] = useState<string>(prefilledViolation || '');
  const [complaintId, setComplaintId] = useState<string>(prefilledComplaint || '');
  const [rectificationDays, setRectificationDays] = useState<number>(30);
  const [notes, setNotes] = useState<string>('');
  const [createdCase, setCreatedCase] = useState<EnforcementCaseResult | null>(null);

  // Fetch product list for dropdown if not prefilled
  const { data: products = [] } = useQuery<ProductSummary[]>({
    queryKey: ['products-list-officer'],
    queryFn: async () => {
      const { data } = await apiClient.get<ProductSummary[] | { results: ProductSummary[] }>('/products/');
      if (Array.isArray(data)) return data;
      if (data && Array.isArray((data as { results: ProductSummary[] }).results)) {
        return (data as { results: ProductSummary[] }).results;
      }
      return [];
    },
  });

  // Fetch violation history for the selected product to determine first-time vs repeat
  const { data: timeline } = useQuery<ProductViolationTimeline>({
    queryKey: ['product-violation-history', productId],
    queryFn: () => fetchProductViolationHistory(productId),
    enabled: Boolean(productId),
  });

  // Fetch recent cases opened by officer
  const { data: recentCasesData = [], isLoading: isLoadingCases } = useQuery<EnforcementCaseResult[]>({
    queryKey: ['officer-cases-list'],
    queryFn: fetchOfficerCases,
  });

  const recentCases: EnforcementCaseResult[] = Array.isArray(recentCasesData)
    ? recentCasesData
    : (recentCasesData as { results?: EnforcementCaseResult[] })?.results ?? [];

  useEffect(() => {
    if (prefilledProduct) setProductId(prefilledProduct);
    if (prefilledViolation) setViolationId(prefilledViolation);
    if (prefilledComplaint) setComplaintId(prefilledComplaint);
  }, [prefilledProduct, prefilledViolation, prefilledComplaint]);

  // Selected violation detail from timeline if available
  const historyList = Array.isArray(timeline?.history) ? timeline.history : [];
  const selectedViolationEntry = historyList.find(
    (h) => String(h.violation_id) === String(violationId)
  );

  const isRepeat = timeline?.has_repeat_offenses || (selectedViolationEntry && !selectedViolationEntry.is_first_time);

  const createCaseMutation = useMutation({
    mutationFn: () =>
      createEnforcementCase({
        product: Number(productId),
        violation: violationId ? Number(violationId) : undefined,
        complaint: complaintId ? Number(complaintId) : undefined,
        rectification_days: rectificationDays,
        notes,
      }),
    onSuccess: (data) => {
      setCreatedCase(data);
      queryClient.invalidateQueries({ queryKey: ['officer-cases-list'] });
      queryClient.invalidateQueries({ queryKey: ['inspection-queue'] });
    },
  });

  const handleCreateCase = (e: React.FormEvent) => {
    e.preventDefault();
    if (!productId) return;
    createCaseMutation.mutate();
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/20 text-primary border border-primary/30">
              Statutory Enforcement Framework
            </span>
            <span className="text-xs text-muted-foreground">Legal Metrology Act, 2009</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground mt-1">
            Initiate Enforcement Case & Statutory Notice
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/officer/queue')}
            className="px-3.5 py-2 rounded-lg bg-card/60 border border-border text-xs font-medium text-muted-foreground hover:text-foreground"
          >
            ← Inspection Queue
          </button>
        </div>
      </div>

      {/* Success Notification / Case Result Card */}
      {createdCase && (
        <div className="glass-card p-6 rounded-2xl border border-emerald-500/40 bg-emerald-950/30 text-emerald-200 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-3xl">⚖️</span>
              <div>
                <h3 className="text-lg font-bold text-white">
                  Case #{createdCase.id} Successfully Opened
                </h3>
                <p className="text-xs text-emerald-300">
                  Target Product: {createdCase.brand_name} — {createdCase.product_name} (GTIN: {createdCase.gtin_barcode})
                </p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 uppercase">
              {createdCase.classification === 'first_time' ? 'Section 29 Notice Issued' : 'Section 39 Penalty Escalated'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 text-xs">
            <div className="p-3 rounded-xl bg-card/50 border border-border/40 space-y-1">
              <span className="text-muted-foreground uppercase font-semibold">Statutory Path</span>
              <p className="font-bold text-foreground">
                {createdCase.classification === 'first_time'
                  ? 'Section 29 Improvement Notice'
                  : 'Section 39 Compounding Penalty'}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-card/50 border border-border/40 space-y-1">
              <span className="text-muted-foreground uppercase font-semibold">
                {createdCase.improvement_notice ? 'Rectification Deadline' : 'Compounding Status'}
              </span>
              <p className="font-bold text-foreground">
                {createdCase.improvement_notice
                  ? `${createdCase.improvement_notice.rectification_deadline} (30 Days)`
                  : 'Awaiting Controller Penalty Order'}
              </p>
            </div>

            <div className="p-3 rounded-xl bg-card/50 border border-border/40 space-y-1">
              <span className="text-muted-foreground uppercase font-semibold">Investigating Officer</span>
              <p className="font-bold text-foreground">{createdCase.opened_by_username}</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              onClick={() => setCreatedCase(null)}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all"
            >
              + File Another Notice
            </button>
            <button
              onClick={() => navigate('/officer/queue')}
              className="px-4 py-2 rounded-lg bg-card border border-border text-xs font-semibold text-foreground hover:bg-card/80 transition-all"
            >
              Return to Queue
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Case Creation Form */}
        <div className="lg:col-span-2 space-y-6">
          <form onSubmit={handleCreateCase} className="glass-card p-6 rounded-2xl border border-border/60 bg-card/50 space-y-6">
            <h2 className="text-base font-bold text-foreground flex items-center gap-2 border-b border-border/40 pb-3">
              <span>📝</span>
              <span>Case Parameter & Notice Generation</span>
            </h2>

            {/* Product Selection */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-foreground uppercase tracking-wider">
                Target Commodity / Product <span className="text-rose-400">*</span>
              </label>
              <select
                value={productId}
                onChange={(e) => {
                  setProductId(e.target.value);
                  setViolationId('');
                }}
                required
                className="w-full px-4 py-2.5 rounded-lg bg-card/80 border border-border text-foreground text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none"
              >
                <option value="">Select target product...</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.brand_name} - {p.product_name} ({p.gtin_barcode})
                  </option>
                ))}
              </select>
            </div>

            {/* Violation Selection from History */}
            {historyList.length > 0 && (
              <div className="space-y-2">
                <label className="text-xs font-bold text-foreground uppercase tracking-wider">
                  Associated Violation Finding (Optional)
                </label>
                <select
                  value={violationId}
                  onChange={(e) => setViolationId(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-lg bg-card/80 border border-border text-foreground text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none"
                >
                  <option value="">Apply to product general non-compliance</option>
                  {historyList.map((h) => (
                    <option key={h.violation_id} value={h.violation_id}>
                      [{h.rule_id_code}] {h.section_ref}: {h.description.slice(0, 60)}... ({h.is_first_time ? '1st Offense' : 'Repeat'})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Dynamic Statutory Classification Banner */}
            {productId && (
              <div
                className={`p-4 rounded-xl border text-xs space-y-2 ${
                  isRepeat
                    ? 'bg-rose-950/30 border-rose-500/40 text-rose-200'
                    : 'bg-amber-950/30 border-amber-500/40 text-amber-200'
                }`}
              >
                <div className="flex items-center gap-2 font-bold text-sm">
                  <span>{isRepeat ? '⚠️ Statutory Escalation: Section 39' : '📋 Statutory Procedure: Section 29'}</span>
                </div>
                <p className="leading-relaxed">
                  {isRepeat
                    ? 'This product/manufacturer has prior recorded non-compliance history. Under the Legal Metrology Act 2009, this case will be filed as a repeat offense and escalated directly to the State Controller for compounding penalty determination.'
                    : 'This is recorded as a first-time violation. A formal Section 29 Improvement Notice will be issued granting the manufacturer a statutory rectification period to correct packaging declarations.'}
                </p>
              </div>
            )}

            {/* Rectification Window */}
            {!isRepeat && (
              <div className="space-y-2">
                <label className="text-xs font-bold text-foreground uppercase tracking-wider">
                  Rectification Period (Days)
                </label>
                <div className="flex items-center gap-3">
                  <input
                    type="number"
                    min={7}
                    max={90}
                    value={rectificationDays}
                    onChange={(e) => setRectificationDays(Number(e.target.value))}
                    className="w-32 px-4 py-2 rounded-lg bg-card/80 border border-border text-foreground text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none"
                  />
                  <span className="text-xs text-muted-foreground">Standard statutory window: 30 days</span>
                </div>
              </div>
            )}

            {/* Officer Inspection Notes */}
            <div className="space-y-2">
              <label className="text-xs font-bold text-foreground uppercase tracking-wider">
                Officer Field Findings & Evidence Summary
              </label>
              <textarea
                rows={3}
                placeholder="Enter field inspection observations, retail premises name, batch details, or non-compliance remarks..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-4 py-2.5 rounded-lg bg-card/80 border border-border text-foreground text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none placeholder:text-muted-foreground"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={createCaseMutation.isPending || !productId}
              className="w-full py-3 rounded-xl font-bold text-primary-foreground bg-primary hover:bg-primary/90 disabled:opacity-50 transition-all shadow-lg flex items-center justify-center gap-2 text-sm"
            >
              {createCaseMutation.isPending ? (
                <>
                  <span className="animate-spin">⚙️</span>
                  <span>Generating Statutory Notice...</span>
                </>
              ) : (
                <>
                  <span>⚖️</span>
                  <span>{isRepeat ? 'Escalate Section 39 Penalty Case' : 'Issue Section 29 Improvement Notice'}</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right 1 Col: Recent Enforcement Cases List */}
        <div className="space-y-4">
          <div className="glass-card p-5 rounded-2xl border border-border/60 bg-card/50 space-y-4">
            <h3 className="text-sm font-bold text-foreground border-b border-border/40 pb-2 flex items-center gap-2">
              <span>🏛️</span>
              <span>Recent Enforcement Cases</span>
            </h3>

            {isLoadingCases ? (
              <p className="text-xs text-muted-foreground text-center py-4">Loading active cases...</p>
            ) : recentCases.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">No enforcement cases opened yet.</p>
            ) : (
              <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
                {recentCases.slice(0, 8).map((c) => (
                  <div
                    key={c.id}
                    className="p-3 rounded-xl bg-card/70 border border-border/50 hover:border-primary/40 transition-all space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-foreground">Case #{c.id}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          c.classification === 'first_time'
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                            : 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        }`}
                      >
                        {c.classification === 'first_time' ? 'Sec 29 Notice' : 'Sec 39 Penalty'}
                      </span>
                    </div>
                    <p className="text-muted-foreground font-medium truncate">
                      {c.brand_name} — {c.product_name}
                    </p>
                    <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-border/30">
                      <span>Status: <strong className="text-foreground">{c.status}</strong></span>
                      <span className="font-mono">
                        {c.created_at ? new Date(c.created_at).toLocaleDateString('en-IN') : ''}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
