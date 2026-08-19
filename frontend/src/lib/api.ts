import type {
  Alert,
  Business,
  BusinessLegalType,
  ComplianceEvaluationResult,
  CopilotAskResponse,
  DigitalTwin,
  DocumentExtractionResponse,
  DocumentType,
  Filing,
  FilingStatus,
  Obligation,
  ObligationStatus,
  Registration,
  RegistrationType,
  SectorType,
  TurnoverBand,
} from '../types'
import { getToken } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export interface HealthResponse {
  status: string
  environment?: string
}

class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...init,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new ApiError(res.status, body || `Request failed: ${res.status}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export async function getBackendHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/v1/health')
}

export interface BusinessCreatePayload {
  name: string
  sector: SectorType
  state: string
  registration_type: BusinessLegalType
  turnover_band: TurnoverBand
  employee_count: number
  incorporation_date?: string | null
  gstin?: string
  udyam_number?: string
  pan?: string
}

export function createBusiness(payload: BusinessCreatePayload): Promise<Business> {
  return request<Business>('/api/v1/business', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function getBusiness(businessId: string): Promise<Business> {
  return request<Business>(`/api/v1/business/${businessId}`)
}

export function createRegistration(
  businessId: string,
  type: RegistrationType,
  number?: string,
): Promise<Registration> {
  return request<Registration>('/api/v1/registrations', {
    method: 'POST',
    body: JSON.stringify({ business_id: businessId, type, status: 'active', number }),
  })
}

export function getTwin(businessId: string): Promise<DigitalTwin> {
  return request<DigitalTwin>(`/api/v1/twin/${businessId}`)
}

export function evaluateCompliance(businessId: string): Promise<ComplianceEvaluationResult> {
  return request<ComplianceEvaluationResult>(`/api/v1/compliance/evaluate/${businessId}`, {
    method: 'POST',
  })
}

export function listObligations(businessId: string): Promise<Obligation[]> {
  return request<Obligation[]>(`/api/v1/obligations?business_id=${businessId}`)
}

export function updateObligationStatus(
  obligationId: string,
  status: ObligationStatus,
): Promise<Obligation> {
  return request<Obligation>(`/api/v1/obligations/${obligationId}`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

export function askCopilot(businessId: string, question: string): Promise<CopilotAskResponse> {
  return request<CopilotAskResponse>(`/api/v1/copilot/ask/${businessId}`, {
    method: 'POST',
    body: JSON.stringify({ question }),
  })
}

export function listAlerts(businessId: string): Promise<Alert[]> {
  return request<Alert[]>(`/api/v1/alerts?business_id=${businessId}`)
}

export function acknowledgeAlert(alertId: string): Promise<Alert> {
  return request<Alert>(`/api/v1/alerts/${alertId}/acknowledge`, {
    method: 'POST',
  })
}

export async function extractDocument(
  documentType: DocumentType,
  file: File,
): Promise<DocumentExtractionResponse> {
  const formData = new FormData()
  formData.append('document_type', documentType)
  formData.append('file', file)

  // Bypass request(): it hardcodes a JSON Content-Type header, but a
  // multipart body needs its boundary set by the browser, which only
  // happens when Content-Type is left unset.
  const res = await fetch(`${API_BASE_URL}/api/v1/documents/extract`, {
    method: 'POST',
    body: formData,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new ApiError(res.status, body || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<DocumentExtractionResponse>
}

export function listFilings(businessId: string, status?: FilingStatus): Promise<Filing[]> {
  const params = new URLSearchParams({ business_id: businessId })
  if (status) params.set('status', status)
  return request<Filing[]>(`/api/v1/filings?${params.toString()}`)
}

export function createFiling(obligationId: string, period?: string): Promise<Filing> {
  return request<Filing>('/api/v1/filings', {
    method: 'POST',
    body: JSON.stringify({ obligation_id: obligationId, period }),
  })
}

export function approveFiling(filingId: string): Promise<Filing> {
  return request<Filing>(`/api/v1/filings/${filingId}/approve`, { method: 'POST' })
}

export function rejectFiling(filingId: string): Promise<Filing> {
  return request<Filing>(`/api/v1/filings/${filingId}/reject`, { method: 'POST' })
}

export function submitFiling(filingId: string): Promise<Filing> {
  return request<Filing>(`/api/v1/filings/${filingId}/submit`, { method: 'POST' })
}
