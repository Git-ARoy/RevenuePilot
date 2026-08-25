export interface DashboardSummary {
  amount_at_risk: number;
  amount_recovered: number;
  recovery_rate: number;
  active_cases: number;
  escalated_cases: number;
  failed_actions: number;
  period?: {
    from: string;
    to: string;
  };
}

export interface RecoveryCase {
  id: string;
  merchant_id?: string;
  payment_id?: string;
  batch_id?: string;
  case_type: string;
  amount_at_risk: number;
  amount_recovered: number;
  currency: string;
  status: string;
  diagnosis_code?: string | null;
  diagnosis_confidence?: number | null;
  recovery_score?: number | null;
  current_strategy?: string | null;
  attempt_count: number;
  max_attempts: number;
  next_eligible_at?: string | null;
  terminal_reason?: string | null;
  created_at: string;
  updated_at?: string | null;
}

export interface PolicyCheckItem {
  rule: string;
  passed: boolean;
  detail: string;
}

export interface PolicyEvaluation {
  allowed: boolean;
  checks: PolicyCheckItem[];
  block_reason?: string | null;
}

export interface CaseEvaluationResult {
  case_id: string;
  diagnosis: {
    code: string;
    confidence: number;
    reason: string;
  };
  candidate_action: {
    type: string;
    reason_code: string;
    confidence: number;
  };
  policy: PolicyEvaluation;
}

export interface AuditEvent {
  id: string;
  recovery_case_id?: string | null;
  event_type: string;
  actor_type: string;
  actor_id?: string | null;
  metadata?: Record<string, any> | null;
  created_at: string;
}

export interface BatchMetrics {
  cases: number;
  eligible_cases?: number;
  amount_at_risk: number;
  amount_recovered: number;
  recovery_rate: number;
  recovered_cases?: number;
  actions_attempted?: number;
  escalations: number;
  terminal_failures: number;
  stopped?: number;
}

export interface BatchRun {
  id: string;
  merchant_id?: string;
  mode: string;
  seed: number;
  config?: Record<string, any>;
  status: string;
  case_count: number;
  amount_at_risk: number;
  amount_recovered: number;
  recovery_rate: number;
  metrics?: BatchMetrics | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
}

export interface PolicyConfig {
  id?: string;
  merchant_id?: string;
  max_attempts: number;
  retry_cooldown_seconds: number;
  max_automated_recovery_amount: number;
  human_approval_threshold: number;
  allowed_actions: string[];
  escalation_threshold?: number;
  model_selection?: string;
  simulation_mode?: boolean;
}

export interface PaginatedCasesResponse {
  items: RecoveryCase[];
  page: number;
  page_size: number;
  total: number;
}
