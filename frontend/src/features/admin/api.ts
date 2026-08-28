/**
 * API client for Rule Engine Admin Console (Phase 4.3).
 * SAFE PAGINATION HANDLING: Every list endpoint extracts `.results` or normalizes array
 * to prevent 'filter is not a function' pagination regressions.
 */
import apiClient from '../../services/apiClient';
import type {
  RuleNotification,
  RuleDraft,
  RuleSimulationResult,
  RuleItem,
  AdminDashboardSummary,
  InspectionWeightConfig,
} from './types';

// Helper to safely unwrap DRF Paginated vs Plain Array responses
function unwrapResults<T>(data: any): T[] {
  if (Array.isArray(data)) {
    return data;
  }
  if (data && Array.isArray(data.results)) {
    return data.results;
  }
  return [];
}

export const adminApi = {
  /**
   * Step A: Fetch incoming detected/seeded notifications
   * GET /api/rules/incoming-notifications/
   */
  async getNotifications(): Promise<RuleNotification[]> {
    const response = await apiClient.get('/rules/incoming-notifications/');
    return unwrapResults<RuleNotification>(response.data);
  },

  /**
   * Step B: Generate structured rule draft from notification or payload
   * POST /api/rules/draft/
   */
  async createDraft(payload: {
    notification_id?: number;
    rule_id_code?: string;
    section_ref?: string;
    category?: string;
    old_clause_text?: string;
    new_clause_text?: string;
    proposed_condition?: Record<string, any>;
  }): Promise<RuleDraft> {
    const response = await apiClient.post<RuleDraft>('/rules/draft/', payload);
    return response.data;
  },

  /**
   * Step C: Retrieve single rule draft details with old vs new diff & simulation history
   * GET /api/rules/{id}/
   */
  async getDraft(id: number | string): Promise<RuleDraft> {
    const response = await apiClient.get<RuleDraft>(`/rules/${id}/`);
    return response.data;
  },

  /**
   * Step D (Yes): Approve draft and set planned effective date
   * POST /api/rules/{id}/approve/
   */
  async approveDraft(
    id: number | string,
    payload: { effective_date: string; comment?: string }
  ): Promise<RuleDraft> {
    const response = await apiClient.post<RuleDraft>(`/rules/${id}/approve/`, payload);
    return response.data;
  },

  /**
   * Step D (No / Revise): Update draft in place with admin edits & log comment
   * POST /api/rules/{id}/revise/
   */
  async reviseDraft(
    id: number | string,
    payload: {
      rule_id_code?: string;
      section_ref?: string;
      category?: string;
      old_clause_text?: string;
      new_clause_text?: string;
      proposed_condition?: Record<string, any>;
      effective_date?: string | null;
      comment?: string;
    }
  ): Promise<RuleDraft> {
    const response = await apiClient.post<RuleDraft>(`/rules/${id}/revise/`, payload);
    return response.data;
  },

  /**
   * Step H6–H7: Run read-only sandbox simulation against historical inspections
   * POST /api/rules/{id}/simulate/
   */
  async simulateDraft(id: number | string): Promise<RuleSimulationResult> {
    const response = await apiClient.post<RuleSimulationResult>(`/rules/${id}/simulate/`);
    return response.data;
  },

  /**
   * Step G: Publish approved rule live into repository with effective date
   * POST /api/rules/{id}/publish/
   */
  async publishDraft(
    id: number | string,
    payload?: { effective_date?: string }
  ): Promise<RuleItem> {
    const response = await apiClient.post<RuleItem>(`/rules/${id}/publish/`, payload || {});
    return response.data;
  },

  /**
   * Live Rule Repository: filterable list with pagination support
   * GET /api/rules/
   */
  async getRules(params?: {
    status?: string;
    category?: string;
    search?: string;
    ordering?: string;
    page?: number;
  }): Promise<{ count: number; results: RuleItem[] }> {
    const response = await apiClient.get('/rules/', { params });
    if (response.data && Array.isArray(response.data.results)) {
      return response.data;
    }
    const arr = unwrapResults<RuleItem>(response.data);
    return { count: arr.length, results: arr };
  },

  /**
   * Step H: Admin Dashboard Analytics Summary
   * GET /api/rules/admin-dashboard/
   */
  async getAdminDashboardSummary(): Promise<AdminDashboardSummary> {
    const response = await apiClient.get<AdminDashboardSummary>('/rules/admin-dashboard/');
    return response.data;
  },

  /**
   * Step I: Get and update dynamic inspection priority weights
   * GET /api/rules/inspection-weights/
   * POST /api/rules/inspection-weights/
   */
  async getInspectionWeights(): Promise<InspectionWeightConfig> {
    const response = await apiClient.get<InspectionWeightConfig>('/rules/inspection-weights/');
    return response.data;
  },

  async updateInspectionWeights(payload: Partial<InspectionWeightConfig>): Promise<InspectionWeightConfig> {
    const response = await apiClient.post<InspectionWeightConfig>('/rules/inspection-weights/', payload);
    return response.data;
  },
};
