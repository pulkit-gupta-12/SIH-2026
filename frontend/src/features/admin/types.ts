/**
 * TypeScript types for Rule Engine Admin Console (Phase 4.3).
 */

export interface RuleNotification {
  id: number;
  notification_no: string;
  title: string;
  source_text: string;
  gazette_url?: string;
  published_date: string;
  date_detected: string;
  category: string;
  status: 'new' | 'drafted' | 'approved' | 'published';
  draft_count?: number;
}

export interface RuleSimulationResult {
  id: number;
  draft: number;
  total_scans_evaluated: number;
  before_compliance_rate: number;
  after_compliance_rate: number;
  projected_violation_diff: number;
  metrics: {
    evaluated_scans_count?: number;
    category?: string;
    condition_type?: string;
    impact_summary?: string;
    category_breakdown?: Record<string, { before_compliant: number; after_compliant: number; new_violations: number }>;
    affected_brands_sample?: string[];
    [key: string]: any;
  };
  created_at: string;
}

export interface DraftComment {
  admin: string;
  action: string;
  comment: string;
  effective_date?: string;
  timestamp: string;
}

export interface RuleDraft {
  id: number;
  notification?: number | null;
  notification_title?: string;
  notification_no?: string;
  rule_id_code: string;
  section_ref: string;
  category: string;
  old_clause_text: string;
  new_clause_text: string;
  proposed_condition: Record<string, any>;
  effective_date?: string | null;
  status: 'pending_review' | 'revised' | 'approved' | 'published';
  comments: DraftComment[];
  reviewing_admin?: number | null;
  reviewing_admin_name?: string;
  supersedes_rule?: number | null;
  supersedes_rule_code?: string;
  simulation_results?: RuleSimulationResult[];
  created_at: string;
  updated_at: string;
}

export interface RuleItem {
  id: number;
  rule_id_code: string;
  section_ref: string;
  category: string;
  condition: Record<string, any>;
  effective_from: string;
  effective_to?: string | null;
  superseded_by?: number | null;
  superseded_by_code?: string | null;
  status: 'draft' | 'in_force' | 'repealed';
  source?: number;
  source_title?: string;
  source_notification_no?: string;
}

export interface AdminKPIs {
  total_active_rules: number;
  pending_drafts: number;
  new_notifications: number;
  total_cases: number;
  open_cases: number;
  escalated_cases: number;
  national_compliance_rate: number;
}

export interface CategoryViolation {
  category: string;
  violations: number;
}

export interface RegionViolation {
  region: string;
  complaints: number;
  inspections: number;
  compliance_rate: number;
}

export interface OfficerPerformance {
  officer_id: number;
  name: string;
  username: string;
  cases_opened: number;
  scans_conducted: number;
  inspections_completed: number;
  inspections_pending: number;
}

export interface AdminDashboardSummary {
  kpis: AdminKPIs;
  violations_by_category: CategoryViolation[];
  violations_by_region: RegionViolation[];
  officer_performance: OfficerPerformance[];
}

export interface InspectionWeightConfig {
  id: number;
  risk_engine_weight: number;
  complaint_weight: number;
  ecommerce_weight: number;
  repeat_offense_multiplier: number;
  category_multipliers: Record<string, number>;
  updated_by_name?: string;
  updated_at: string;
}
