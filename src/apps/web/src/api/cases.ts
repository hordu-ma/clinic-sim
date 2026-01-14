import request from './request'

export interface Case {
  id: number
  title: string
  chief_complaint: string
  department: string
  difficulty: string
  visit_time: string
}

export interface AvailableTestItem {
  type: string
  name: string
}

export interface AvailableTestsResponse {
  case_id: number
  items: AvailableTestItem[]
  total: number
}

// 获取病例列表
export function getCaseList(params?: any) {
  return request.get<any, Case[]>('/cases', { params })
}

// 获取病例详情
export function getCaseDetail(id: number) {
  return request.get<any, Case>(`/cases/${id}`)
}

// 获取可用检查
export function getAvailableTests(caseId: number) {
  return request.get<any, AvailableTestsResponse>(`/cases/${caseId}/available-tests`)
}
