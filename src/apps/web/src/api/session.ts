import request from "./request";

export interface Session {
  id: string;
  case_id: string;
  user_id: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface CreateSessionParams {
  case_id: string;
}

export interface ApplyTestParams {
  test_type: string;
}

export interface SubmitDiagnosisParams {
  diagnosis: string;
}

export interface SessionResult {
  total_score: number;
  feedback: string;
  details: Record<string, any>;
}

// 获取会话列表
export function getSessions() {
  return request.get<any, Session[]>("/sessions");
}

// 创建会话
export function createSession(data: CreateSessionParams) {
  return request.post<any, Session>("/sessions", data);
}

// 获取会话详情
export function getSession(sessionId: string) {
  return request.get<any, Session>(`/sessions/${sessionId}`);
}

// 获取会话消息历史
export function getSessionMessages(sessionId: string) {
  return request.get<any, Message[]>(`/sessions/${sessionId}/messages`);
}

// 申请检查
export function applyTest(sessionId: string, data: ApplyTestParams) {
  return request.post<any, Message>(`/sessions/${sessionId}/tests`, data);
}

// 提交诊断
export function submitDiagnosis(
  sessionId: string,
  data: SubmitDiagnosisParams
) {
  return request.post<any, SessionResult>(
    `/sessions/${sessionId}/diagnosis`,
    data
  );
}
