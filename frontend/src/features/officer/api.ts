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
  created_at: string;
}

export interface ScanProcessingResult {
  id: number;
  product: number;
  performed_by: number;
  role_context: string;
  location: string;
  capture_method: string;
  status: string;
  scan_images: Array<{ id: number; image_url: string; angle: string }>;
  extracted_fields: ExtractedFieldItem[];
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
  const { data } = await apiClient.get<InspectionQueueItem[]>('/inspections/queue/');
  return data;
}

export async function submitOfficerGuidedScan(payload: {
  barcode: string;
  category: string;
  image_urls: string[];
  location?: string;
}): Promise<ScanProcessingResult> {
  const { data } = await apiClient.post<ScanProcessingResult>('/scans/', {
    ...payload,
    role_context: 'officer',
    capture_method: 'guided_capture',
  });
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
  const { data } = await apiClient.get<EnforcementCaseResult[]>('/cases/');
  return data;
}
