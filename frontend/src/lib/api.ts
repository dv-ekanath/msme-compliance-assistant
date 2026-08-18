import type {
  Business,
  BusinessLegalType,
  ComplianceEvaluationResult,
  DigitalTwin,
  Obligation,
  ObligationStatus,
  Registration,
  RegistrationType,
  SectorType,
  TurnoverBand,
} from '../types'

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
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
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
): Promise<Registration> {
  return request<Registration>('/api/v1/registrations', {
    method: 'POST',
    body: JSON.stringify({ business_id: businessId, type, status: 'active' }),
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
