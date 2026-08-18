// Mirrors backend/app/domain/enums.py and backend/app/schemas/*.py.
// Kept as plain string-literal unions (not generated) -- Phase 1 scope.

export type SectorType = 'manufacturing' | 'trading' | 'services' | 'other'

export type BusinessLegalType =
  | 'proprietorship'
  | 'partnership'
  | 'llp'
  | 'private_limited'
  | 'public_limited'
  | 'huf'
  | 'other'

export type TurnoverBand =
  | 'under_10l'
  | '10l_20l'
  | '20l_40l'
  | '40l_5cr'
  | '5cr_50cr'
  | '50cr_250cr'
  | 'above_250cr'

export type RegistrationType =
  | 'gst'
  | 'udyam'
  | 'shops_establishment'
  | 'epf'
  | 'esi'
  | 'professional_tax'
  | 'other'

export type RegistrationStatus = 'active' | 'inactive' | 'pending' | 'expired'

export type ObligationType = 'registration' | 'filing' | 'renewal' | 'payment'

export type ObligationFrequency = 'one_time' | 'monthly' | 'quarterly' | 'annually'

export type ObligationApplicability = 'applicable' | 'not_applicable' | 'review_required'

export type ObligationStatus = 'pending' | 'due_soon' | 'overdue' | 'completed'

export interface Business {
  id: string
  name: string
  sector: SectorType
  state: string
  registration_type: BusinessLegalType
  turnover_band: TurnoverBand
  employee_count: number
  incorporation_date: string | null
  udyam_number: string | null
  gstin: string | null
  pan: string | null
  address: string | null
  contact_phone: string | null
  contact_email: string | null
  created_at: string
  updated_at: string
}

export interface Registration {
  id: string
  business_id: string
  type: RegistrationType
  number: string | null
  status: RegistrationStatus
  valid_from: string | null
  valid_to: string | null
  document_ref: string | null
  created_at: string
  updated_at: string
}

export interface Obligation {
  id: string
  business_id: string
  regulation_id: string
  rule_id: string
  obligation_type: ObligationType
  title: string
  reason: string
  frequency: ObligationFrequency | null
  due_date: string | null
  applicability: ObligationApplicability
  status: ObligationStatus
  risk_score: number | null
  last_evaluated_at: string
}

export interface ComplianceSummary {
  total_applicable: number
  completed: number
  due_soon: number
  overdue: number
  review_required: number
  compliance_health: 'good' | 'attention_needed' | 'critical'
}

export interface DigitalTwin {
  business: Business
  registrations: Registration[]
  employee_count: number
  obligations: Obligation[]
  summary: ComplianceSummary
  upcoming_deadlines: Obligation[]
}

export interface ComplianceResultItem {
  rule_id: string
  obligation: string
  obligation_type: ObligationType
  applicability: ObligationApplicability
  status: ObligationStatus
  reason: string
  regulation: string
  regulation_code: string
  source_url: string
  frequency: ObligationFrequency | null
  due_date: string | null
}

export interface ComplianceEvaluationResult {
  business_id: string
  evaluated_at: string
  results: ComplianceResultItem[]
  summary: ComplianceSummary
}
