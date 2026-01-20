import request from "./request";
import type {
  SessionResponse,
  SessionListResponse,
  SessionListItem,
  SessionDetail,
  TestRequestCreate,
  TestRequestResponse,
  DiagnosisSubmitRequest,
  DiagnosisSubmitResponse,
} from "../types";

// 获取会话列表
export function getSessions(params?: {
  status?: string;
  skip?: number;
  limit?: number;
}) {
  return request.get<any, SessionListResponse>("/sessions/", { params });
}

// 创建会话
export function createSession(data: { mode?: "fixed" | "random"; case_id?: number }) {
  return request.post<any, SessionResponse>("/sessions/", data);
}

// 获取会话详情
export function getSession(sessionId: number) {
  return request.get<any, SessionDetail>(`/sessions/${sessionId}`);
}

// 获取会话消息历史（从 SessionDetail 中获取）
export function getSessionMessages(sessionId: number) {
  return getSession(sessionId).then((res) => res.messages);
}

// 申请检查
export function applyTest(sessionId: number, data: TestRequestCreate) {
  return request.post<any, TestRequestResponse>(
    `/sessions/${sessionId}/tests`,
    data
  );
}

// 提交诊断
export function submitDiagnosis(
  sessionId: number,
  data: DiagnosisSubmitRequest
) {
  return request.post<any, DiagnosisSubmitResponse>(
    `/sessions/${sessionId}/submit`,
    data
  );
}

// Re-export types for convenience
export type {
  SessionResponse,
  SessionListResponse,
  SessionListItem,
  SessionDetail,
  TestRequestResponse,
  DiagnosisSubmitResponse,
};
