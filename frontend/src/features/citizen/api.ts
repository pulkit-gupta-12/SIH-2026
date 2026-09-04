import apiClient from "../../services/apiClient";

export interface ViolationItem {
  rule_id: number;
  rule_code: string | null;
  rule_name?: string | null;
  section_ref?: string | null;
  description?: string | null;
  field?: string | null;
  is_first_time?: boolean | null;
}

export interface ComplianceSnapshot {
  product_id: number;
  product_name: string;
  brand_name: string | null;
  gtin_barcode: string | null;
  category?: string | null;
  has_been_scanned: boolean;
  verdict: "compliant" | "non_compliant" | "needs_review" | "unknown" | string;
  last_checked_at: string | null;
  violation_count: number;
  violations: ViolationItem[];
}

export interface Product {
  id: number;
  gtin_barcode: string | null;
  brand_name: string;
  product_name: string;
  category: string;
  manufacturer_name: string;
  manufacturer_address: string;
  registered_by_business?: number | null;
  created_at: string;
  [key: string]: unknown;
}

export interface Complaint {
  id: number;
  product: number;
  product_name?: string;
  brand_name?: string;
  gtin_barcode?: string;
  description: string;
  photo_urls: string[];
  location?: string | null;
  risk_score: number;
  routed_to_state?: string | null;
  status: string;
  filed_by?: number;
  filed_by_username?: string;
  created_at: string;
}

/** Scan/Search: looks up barcode or submits 1 photo if product is first-time */
export async function scanOrLookupProduct(params: {
  barcode?: string;
  imageUrl?: string;
  category?: string;
}): Promise<ComplianceSnapshot> {
  if (!params.imageUrl) {
    const payload: Record<string, unknown> = {};
    if (params.barcode) payload.barcode = params.barcode;
    if (params.category) payload.category = params.category;
    const { data } = await apiClient.post<ComplianceSnapshot>("/scans/", payload);
    return data;
  }

  const formData = new FormData();
  if (params.barcode) formData.append('barcode', params.barcode);
  if (params.category) formData.append('category', params.category);
  const response = await fetch(params.imageUrl);
  const blob = await response.blob();
  formData.append('images', blob, `citizen-scan.${blob.type.split('/')[1] || 'jpg'}`);

  const { data } = await apiClient.post<ComplianceSnapshot>("/scans/", formData);
  return data;
}

/** Manual text search fallback on Scan/Search screen */
export async function searchProducts(query: string): Promise<Product[]> {
  const { data } = await apiClient.get<Product[] | { results: Product[] }>("/products/", {
    params: { q: query },
  });
  if (Array.isArray(data)) return data;
  if (data && Array.isArray((data as { results: Product[] }).results)) {
    return (data as { results: Product[] }).results;
  }
  return [];
}

/** Compliance Snapshot: GET /api/products/{id}/compliance-snapshot/ */
export async function getComplianceSnapshot(productId: number): Promise<ComplianceSnapshot> {
  const { data } = await apiClient.get<ComplianceSnapshot>(
    `/products/${productId}/compliance-snapshot/`
  );
  return data;
}

/** Product/Brand info detail: GET /api/products/{id}/ */
export async function getProduct(productId: number): Promise<Product> {
  const { data } = await apiClient.get<Product>(`/products/${productId}/`);
  return data;
}

/** File complaint: POST /api/complaints/ */
export async function fileComplaint(payload: {
  product: number;
  description: string;
  photo_urls?: string[];
  location?: string;
}): Promise<Complaint> {
  const { data } = await apiClient.post<Complaint>("/complaints/", payload);
  return data;
}

/** Get citizen's own complaints: GET /api/complaints/mine/ */
export async function getMyComplaints(): Promise<Complaint[]> {
  const { data } = await apiClient.get<Complaint[] | { results: Complaint[] }>("/complaints/mine/");
  if (Array.isArray(data)) return data;
  if (data && Array.isArray((data as { results: Complaint[] }).results)) {
    return (data as { results: Complaint[] }).results;
  }
  return [];
}
