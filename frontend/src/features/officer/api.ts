import apiClient from '../../services/apiClient';

export interface InspectionQueueItem {
  id: string | number;
  product: number;
  product_detail: {
    id: number;
    gtin_barcode: string;
    brand_name: string;
    product_name: string;
    category: string;
    manufacturer_name: string;
    manufacturer_address: string;
  };
  assigned_to: number;
  assigned_to_username: string;
  source: 'risk_engine' | 'complaint' | 'ecommerce_flag';
  priority_score: number;
  complaint?: number;
  complaint_detail?: {
    id: number;
    description: string;
    photo_urls: string[];
    location: string;
    risk_score: number;
    routed_to_state: string;
    status: string;
    created_at: string;
  };
  status: 'pending' | 'in_progress' | 'done';
  created_at: string;
}

export interface ExtractedFieldItem {
  id: number;
  field_type: string;
  extracted_value: string;
  confidence_score: number;
  font_size_mm?: number;
  placement_zone?: string;
}

export interface ViolationItem {
  id: number;
  rule_id_code: string;
  section_ref: string;
  description: string;
  field?: string;
  is_first_time: boolean;
  created_at: string;
}

export interface RuleFinding {
  rule_id: string;
  section_ref: string;
  title: string;
  status: 'PASS' | 'FAIL' | 'WARNING' | 'REVIEW' | 'NOT_APPLICABLE';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  detected_value: string;
  expected: string;
  reason: string;
  evidence: {
    field?: string | null;
    raw_text?: string | null;
    source_panel?: string;
    normalized_value?: any;
    bounding_box?: number[] | null;
    matched_snippets?: string[];
  };
  source_panel: string;
  confidence: number;
  requires_human_review: boolean;
  evaluation_source?: string;
}

export interface ReportSummary {
  total_rules: number;
  passed: number;
  failed: number;
  warnings: number;
  review_required: number;
  not_applicable: number;
}

export interface EvidenceItem {
  field: string;
  raw_text: string | null;
  normalized_value: any;
  confidence: number;
  source_panel: string;
  bounding_box?: number[] | null;
  detected: boolean;
  normalization_status: string;
  ambiguity?: string | null;
  barcode?: string;
}

export interface ComplianceReport {
  inspection_id: string;
  overall_status: 'COMPLIANT' | 'NON_COMPLIANT' | 'NEEDS_REVIEW';
  summary: ReportSummary;
  violations: RuleFinding[];
  warnings: RuleFinding[];
  reviews: RuleFinding[];
  passed_rules: RuleFinding[];
  evidence: EvidenceItem[];
  generated_at: string;
}

export interface ComplianceCheckResult {
  id: number;
  scan: number;
  product_id: number;
  product_name: string;
  brand_name: string;
  verdict: 'compliant' | 'non_compliant' | 'needs_review';
  overall_confidence: number;
  evaluated_against_rule_set_date: string;
  reviewed_by_officer?: number;
  reviewed_by_officer_username?: string;
  violations: ViolationItem[];
  report_data?: ComplianceReport;
  created_at: string;
}

export interface CanonicalField<T = any> {
  raw: string | null;
  normalized: T | null;
  confidence: number | null;
  source_panel: string | null;
  bbox: number[] | null;
  detected: boolean;
  normalization_status: 'success' | 'failed' | 'ambiguous' | 'not_detected';
  ambiguity: string | null;
}

export interface NormalizedMrp {
  amount: number;
  currency: string;
  inclusive_of_taxes?: boolean | null;
}

export interface NormalizedQuantity {
  quantity: number;
  unit: string;
}

export interface NormalizedUnitPrice {
  amount: number;
  currency: string;
  unit: string;
}

export interface NormalizedDate {
  year: number;
  month?: number | null;
  day?: number | null;
  date_iso: string;
}

export interface CanonicalPackageData {
  mrp: CanonicalField<NormalizedMrp>;
  net_quantity: CanonicalField<NormalizedQuantity>;
  unit_sale_price: CanonicalField<NormalizedUnitPrice>;
  mfg_date: CanonicalField<NormalizedDate>;
  expiry_date: CanonicalField<NormalizedDate>;
  best_before_date: CanonicalField<any>;
  fssai_license_no: CanonicalField<{ license_number: string; is_valid_format: boolean }>;
  batch_number: CanonicalField<{ batch_number: string }>;
  consumer_care_details: CanonicalField<{ phone?: string; email?: string; address?: string; website?: string }>;
  country_of_origin: CanonicalField<{ country: string; iso_code?: string }>;
  manufacturer_name: CanonicalField<{ name: string }>;
  manufacturer_address: CanonicalField<{ full_address: string; pin_code?: string; city?: string; state?: string }>;
  commodity_name: CanonicalField<{ commodity_name: string }>;
  barcode: CanonicalField<{ barcode: string; type?: string }>;
  other_fields?: Record<string, CanonicalField>;
  raw_text?: string | null;
  metadata?: {
    fields_detected_count: number;
    fields_normalized_count: number;
    overall_status: 'complete' | 'partial' | 'empty';
  };
}

export interface ScanProcessingResult {
  id: number;
  product: number;
  performed_by: number;
  role_context: string;
  location: string;
  capture_method: string;
  status: string;
  scan_images: Array<{ id: number; image_url: string; angle?: string; angle_type?: string }>;
  extracted_fields: ExtractedFieldItem[];
  canonical_data?: CanonicalPackageData & {
    compliance_report?: ComplianceReport;
  };
  compliance_check?: ComplianceCheckResult;
  created_at: string;
}

export interface ProductViolationTimeline {
  product_id: number;
  product_name: string;
  brand_name: string;
  gtin_barcode: string;
  total_violations: number;
  has_repeat_offenses: boolean;
  history: Array<{
    id: number;
    violation_id: number;
    rule_id_code: string;
    section_ref: string;
    description: string;
    is_first_time: boolean;
    case_id?: number;
    case_status?: string;
    created_at: string;
  }>;
}

export interface EnforcementCaseResult {
  id: number;
  product: number;
  product_name: string;
  brand_name: string;
  gtin_barcode: string;
  violation?: number;
  rule_id_code?: string;
  violation_description?: string;
  complaint?: number;
  classification: 'first_time' | 'repeat' | 'fraud';
  status: string;
  opened_by: number;
  opened_by_username: string;
  improvement_notice?: {
    id: number;
    rectification_deadline: string;
    business_response?: string;
    outcome: string;
  };
  penalty_case?: {
    id: number;
    payment_status: string;
    appeal_status: string;
  };
  created_at: string;
}

export async function fetchInspectionQueue(): Promise<InspectionQueueItem[]> {
  const { data } = await apiClient.get<InspectionQueueItem[] | { results: InspectionQueueItem[] }>('/inspections/queue/');
  if (Array.isArray(data)) return data;
  if (data && Array.isArray((data as { results?: InspectionQueueItem[] }).results)) {
    return (data as { results: InspectionQueueItem[] }).results;
  }
  return [];
}

export async function submitOfficerGuidedScan(payload: {
  barcode: string;
  category: string;
  image_urls: string[];
  location?: string;
}): Promise<ScanProcessingResult> {
  const formData = new FormData();
  formData.append('barcode', payload.barcode);
  formData.append('category', payload.category);
  formData.append('location', payload.location || '');
  formData.append('role_context', 'officer');
  formData.append('capture_method', 'guided_capture');

  for (const [index, imageUrl] of payload.image_urls.entries()) {
    const response = await fetch(imageUrl);
    const blob = await response.blob();
    formData.append('images', blob, `capture-${index + 1}.${blob.type.split('/')[1] || 'jpg'}`);
  }

  const { data } = await apiClient.post<ScanProcessingResult>('/scans/', formData);
  return data;
}

export async function fetchProcessingResult(scanId: string | number): Promise<ScanProcessingResult> {
  const { data } = await apiClient.get<ScanProcessingResult>(`/scans/${scanId}/processing-result/`);
  return data;
}

export async function confirmComplianceFinding(
  checkId: string | number
): Promise<{ message: string; compliance_check: ComplianceCheckResult }> {
  const { data } = await apiClient.post<{ message: string; compliance_check: ComplianceCheckResult }>(
    `/compliance-checks/${checkId}/confirm/`
  );
  return data;
}

export async function overrideComplianceFinding(
  checkId: string | number,
  payload: { verdict: string; notes?: string }
): Promise<{ message: string; compliance_check: ComplianceCheckResult }> {
  const { data } = await apiClient.post<{ message: string; compliance_check: ComplianceCheckResult }>(
    `/compliance-checks/${checkId}/override/`,
    payload
  );
  return data;
}

export async function fetchProductViolationHistory(productId: string | number): Promise<ProductViolationTimeline> {
  const { data } = await apiClient.get<ProductViolationTimeline>(`/products/${productId}/violation-history/`);
  if (data && !Array.isArray(data.history)) {
    data.history = [];
  }
  return data;
}

export async function createEnforcementCase(payload: {
  product: number;
  violation?: number;
  complaint?: number;
  rectification_days?: number;
  notes?: string;
}): Promise<EnforcementCaseResult> {
  const { data } = await apiClient.post<EnforcementCaseResult>('/cases/', payload);
  return data;
}

export async function fetchOfficerCases(): Promise<EnforcementCaseResult[]> {
  const { data } = await apiClient.get<EnforcementCaseResult[] | { results: EnforcementCaseResult[] }>('/cases/');
  if (Array.isArray(data)) return data;
  if (data && Array.isArray((data as { results?: EnforcementCaseResult[] }).results)) {
    return (data as { results: EnforcementCaseResult[] }).results;
  }
  return [];
}

export interface ReportResult {
  id: number;
  report_code: string;
  case_id?: number | null;
  compliance_check_id?: number | null;
  file_url: string;
  format: string;
  signed: boolean;
  generated_at: string;
}

export async function generateCaseReport(caseId: string | number, regenerate = false): Promise<ReportResult> {
  const { data } = await apiClient.post<ReportResult>(`/cases/${caseId}/generate-report/`, { regenerate });
  return data;
}

export async function generateCheckReport(checkId: string | number, regenerate = false): Promise<ReportResult> {
  const { data } = await apiClient.post<ReportResult>(`/compliance-checks/${checkId}/generate-report/`, { regenerate });
  return data;
}

export async function fetchLatestReport(params: { caseId?: string | number; checkId?: string | number }): Promise<ReportResult | null> {
  try {
    if (params.caseId) {
      const { data } = await apiClient.get<ReportResult>(`/cases/${params.caseId}/report/`);
      return data;
    }
    if (params.checkId) {
      const { data } = await apiClient.get<ReportResult>(`/compliance-checks/${params.checkId}/report/`);
      return data;
    }
    return null;
  } catch {
    return null;
  }
}
