/**
 * API 响应类型定义
 * 与后端 Pydantic schemas 对齐
 */

// ==================== Auth ====================
export interface Token {
  access_token: string;
  token_type: string;
}

export interface UserResponse {
  id: number;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

// ==================== Cases ====================
export interface CaseListItem {
  id: number;
  title: string;
  chief_complaint: string;
  department: string;
  difficulty: string;
  visit_time: string;
}

export interface AvailableTestItem {
  type: string;
  name: string;
}

export interface AvailableTestsResponse {
  case_id: number;
  items: AvailableTestItem[];
  total: number;
}

// ==================== Sessions ====================
export interface SessionResponse {
  id: number;
  case_id: number;
  status: string;
  started_at: string;
}

export interface SessionListItem {
  id: number;
  case_id: number;
  case_title: string;
  case_difficulty: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  message_count: number;
}

export interface SessionListResponse {
  items: SessionListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface MessageItem {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  tokens: number | null;
  latency_ms: number | null;
  created_at: string;
}

export interface SessionDetail {
  id: number;
  case_id: number;
  case_title: string;
  case_difficulty: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  submitted_diagnosis: string | null;
  messages: MessageItem[];
}

// ==================== Tests ====================
export interface TestRequestCreate {
  test_type: string;
}

export interface TestRequestResponse {
  id: number;
  session_id: number;
  test_type: string;
  test_name: string;
  result: Record<string, any>;
  requested_at: string;
}

export interface TestRequestListItem {
  id: number;
  test_type: string;
  test_name: string;
  result: Record<string, any>;
  requested_at: string;
}

export interface TestRequestListResponse {
  items: TestRequestListItem[];
  total: number;
}

// ==================== Scores ====================
export interface ScoreDimensions {
  interview_completeness: number;
  test_appropriateness: number;
  diagnosis_accuracy: number;
}

export interface ScoringDetails {
  keywords_asked: string[];
  key_points_covered: string[];
  key_points_total: string[];
  tests_requested: string[];
  recommended_tests: string[];
  diagnosis_keywords_matched: string[];
  standard_diagnosis: string;
  submitted_diagnosis: string;
  scoring_rule_version: string;
}

export interface ScoreResponse {
  id: number;
  session_id: number;
  total_score: number;
  dimensions: ScoreDimensions;
  scoring_details: ScoringDetails;
  scoring_method: string;
  model_version: string | null;
  scored_at: string;
}

export interface DiagnosisSubmitRequest {
  diagnosis: string;
}

export interface DiagnosisSubmitResponse {
  session_id: number;
  status: string;
  submitted_diagnosis: string;
  score: ScoreResponse;
}
