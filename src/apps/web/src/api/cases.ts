import request from "./request";
import type {
  CaseListItem,
  CaseDetail,
  AvailableTestItem,
  AvailableTestsResponse,
} from "../types";

// 获取病例列表
export function getCaseList(params?: {
  difficulty?: string;
  department?: string;
  skip?: number;
  limit?: number;
}) {
  return request.get<any, CaseListItem[]>("/cases/", { params });
}

// 获取病例详情
export function getCaseDetail(id: number) {
  return request.get<any, CaseDetail>(`/cases/${id}`);
}

// 获取可用检查
export function getAvailableTests(caseId: number) {
  return request.get<any, AvailableTestsResponse>(
    `/cases/${caseId}/available-tests`
  );
}

// Re-export types
export type {
  CaseListItem,
  CaseDetail,
  AvailableTestItem,
  AvailableTestsResponse,
};
