import { useState, type ChangeEvent, type FormEvent, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import { createBusiness, createRegistration, evaluateCompliance, extractDocument } from '../lib/api'
import type { BusinessLegalType, DocumentType, RegistrationType, SectorType, TurnoverBand } from '../types'

const DOCUMENT_TYPES: { value: DocumentType; label: string }[] = [
  { value: 'gst_certificate', label: 'GST Registration Certificate' },
  { value: 'udyam_certificate', label: 'Udyam Registration Certificate' },
  { value: 'pan_card', label: 'PAN Card' },
]

const SECTORS: { value: SectorType; label: string }[] = [
  { value: 'trading', label: 'Trading / Goods' },
  { value: 'manufacturing', label: 'Manufacturing' },
  { value: 'services', label: 'Services' },
  { value: 'other', label: 'Other' },
]

const LEGAL_TYPES: { value: BusinessLegalType; label: string }[] = [
  { value: 'proprietorship', label: 'Proprietorship' },
  { value: 'partnership', label: 'Partnership' },
  { value: 'llp', label: 'LLP' },
  { value: 'private_limited', label: 'Private Limited' },
  { value: 'public_limited', label: 'Public Limited' },
  { value: 'huf', label: 'HUF' },
  { value: 'other', label: 'Other' },
]

const TURNOVER_BANDS: { value: TurnoverBand; label: string }[] = [
  { value: 'under_10l', label: 'Under ₹10 lakh' },
  { value: '10l_20l', label: '₹10 lakh – ₹20 lakh' },
  { value: '20l_40l', label: '₹20 lakh – ₹40 lakh' },
  { value: '40l_5cr', label: '₹40 lakh – ₹5 crore' },
  { value: '5cr_50cr', label: '₹5 crore – ₹50 crore' },
  { value: '50cr_250cr', label: '₹50 crore – ₹250 crore' },
  { value: 'above_250cr', label: 'Above ₹250 crore' },
]

const REGISTRATION_FLAGS: { key: RegistrationType; label: string }[] = [
  { key: 'gst', label: 'Already GST registered' },
  { key: 'udyam', label: 'Already Udyam registered' },
  { key: 'epf', label: 'Already EPF registered' },
  { key: 'esi', label: 'Already ESI registered' },
]

export default function Onboarding() {
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [sector, setSector] = useState<SectorType>('trading')
  const [state, setState] = useState('')
  const [legalType, setLegalType] = useState<BusinessLegalType>('proprietorship')
  const [turnoverBand, setTurnoverBand] = useState<TurnoverBand>('under_10l')
  const [employeeCount, setEmployeeCount] = useState(0)
  const [incorporationDate, setIncorporationDate] = useState('')
  const [flags, setFlags] = useState<Record<RegistrationType, boolean>>({
    gst: false,
    udyam: false,
    epf: false,
    esi: false,
    shops_establishment: false,
    professional_tax: false,
    other: false,
  })

  const [gstin, setGstin] = useState('')
  const [udyamNumber, setUdyamNumber] = useState('')
  const [pan, setPan] = useState('')

  const [docType, setDocType] = useState<DocumentType>('gst_certificate')
  const [docFile, setDocFile] = useState<File | null>(null)
  const [docStatus, setDocStatus] = useState<'idle' | 'analyzing' | 'done' | 'error'>('idle')
  const [docFieldsFound, setDocFieldsFound] = useState<string[]>([])
  const [docWarning, setDocWarning] = useState<string | null>(null)

  function toggleFlag(key: RegistrationType) {
    setFlags((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  async function handleDocUpload(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setDocFile(file)
    setDocStatus('analyzing')
    setDocWarning(null)
    setDocFieldsFound([])

    try {
      const result = await extractDocument(docType, file)
      const found: string[] = []
      if (result.fields.gstin) {
        setGstin(result.fields.gstin)
        setFlags((prev) => ({ ...prev, gst: true }))
        found.push(`GSTIN ${result.fields.gstin}`)
      }
      if (result.fields.udyam_number) {
        setUdyamNumber(result.fields.udyam_number)
        setFlags((prev) => ({ ...prev, udyam: true }))
        found.push(`Udyam Number ${result.fields.udyam_number}`)
      }
      if (result.fields.pan) {
        setPan(result.fields.pan)
        found.push(`PAN ${result.fields.pan}`)
      }
      setDocFieldsFound(found)
      setDocWarning(result.warning)
      setDocStatus('done')
    } catch {
      setDocStatus('error')
    }
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const business = await createBusiness({
        name,
        sector,
        state,
        registration_type: legalType,
        turnover_band: turnoverBand,
        employee_count: employeeCount,
        incorporation_date: incorporationDate || null,
        gstin: gstin.trim() || undefined,
        udyam_number: udyamNumber.trim() || undefined,
        pan: pan.trim() || undefined,
      })

      const activeFlags = REGISTRATION_FLAGS.filter((f) => flags[f.key])
      await Promise.all(
        activeFlags.map((f) => {
          const number =
            f.key === 'gst' ? gstin.trim() || undefined : f.key === 'udyam' ? udyamNumber.trim() || undefined : undefined
          return createRegistration(business.id, f.key, number)
        }),
      )

      await evaluateCompliance(business.id)

      localStorage.setItem('lastBusinessId', business.id)
      navigate(`/dashboard/${business.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Nav />
      <main className="mx-auto max-w-2xl px-6 py-10">
        <h1 className="mb-1 text-xl font-semibold">Business Onboarding</h1>
        <p className="mb-6 text-sm text-slate-500">
          Tell us about your business. We'll build your Compliance Digital Twin and evaluate
          applicable obligations immediately.
        </p>

        <div className="mb-6 rounded-lg border border-dashed border-slate-300 bg-slate-50 p-5">
          <p className="mb-1 text-sm font-medium text-slate-700">Quick Start — Upload a document</p>
          <p className="mb-3 text-xs text-slate-500">
            Upload a photo of a GST certificate, Udyam certificate, or PAN card (JPEG/PNG) to
            auto-fill the fields below. This runs real OCR — always double-check the extracted
            value before submitting.
          </p>
          <div className="mb-3">
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value as DocumentType)}
              className="input"
            >
              {DOCUMENT_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <input
            type="file"
            accept=".jpg,.jpeg,.png"
            onChange={handleDocUpload}
            className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-900 file:px-3 file:py-1.5 file:text-sm file:font-medium file:text-white hover:file:bg-slate-700"
          />
          {docStatus === 'analyzing' && (
            <p className="mt-3 flex items-center gap-2 text-sm text-slate-500">
              <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-300 border-t-slate-600" />
              Reading {docFile?.name}…
            </p>
          )}
          {docStatus === 'error' && (
            <p className="mt-3 text-sm text-red-600">
              Could not process that document. Please try again or enter the details manually below.
            </p>
          )}
          {docStatus === 'done' && docFieldsFound.length > 0 && (
            <div className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
              Detected from your document: {docFieldsFound.join(', ')} — please verify below before
              submitting.
            </div>
          )}
          {docStatus === 'done' && docWarning && (
            <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
              {docWarning}
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 rounded-lg border border-slate-200 bg-white p-6">
          <Field label="Business name">
            <input
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input"
              placeholder="e.g. Ganga Textiles"
            />
          </Field>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Sector">
              <select value={sector} onChange={(e) => setSector(e.target.value as SectorType)} className="input">
                {SECTORS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Legal structure">
              <select
                value={legalType}
                onChange={(e) => setLegalType(e.target.value as BusinessLegalType)}
                className="input"
              >
                {LEGAL_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="State">
              <input
                required
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="input"
                placeholder="e.g. Maharashtra"
              />
            </Field>
            <Field label="Incorporation date">
              <input
                type="date"
                value={incorporationDate}
                onChange={(e) => setIncorporationDate(e.target.value)}
                className="input"
              />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <Field label="Annual turnover band">
              <select
                value={turnoverBand}
                onChange={(e) => setTurnoverBand(e.target.value as TurnoverBand)}
                className="input"
              >
                {TURNOVER_BANDS.map((b) => (
                  <option key={b.value} value={b.value}>
                    {b.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Employee count">
              <input
                type="number"
                min={0}
                value={employeeCount}
                onChange={(e) => setEmployeeCount(Number(e.target.value))}
                className="input"
              />
            </Field>
          </div>

          <fieldset>
            <legend className="mb-2 text-sm font-medium text-slate-700">
              Existing registrations (check any that already apply)
            </legend>
            <div className="grid grid-cols-2 gap-2">
              {REGISTRATION_FLAGS.map((f) => (
                <label key={f.key} className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={flags[f.key]}
                    onChange={() => toggleFlag(f.key)}
                    className="h-4 w-4 rounded border-slate-300"
                  />
                  {f.label}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="mb-2 text-sm font-medium text-slate-700">
              Registration numbers (auto-filled from an uploaded document, or enter manually)
            </legend>
            <div className="grid grid-cols-3 gap-4">
              <Field label="GSTIN">
                <input
                  value={gstin}
                  onChange={(e) => setGstin(e.target.value)}
                  className="input"
                  placeholder="22AAAAA0000A1Z5"
                />
              </Field>
              <Field label="Udyam Number">
                <input
                  value={udyamNumber}
                  onChange={(e) => setUdyamNumber(e.target.value)}
                  className="input"
                  placeholder="UDYAM-XX-00-0000000"
                />
              </Field>
              <Field label="PAN">
                <input
                  value={pan}
                  onChange={(e) => setPan(e.target.value)}
                  className="input"
                  placeholder="ABCDE1234F"
                />
              </Field>
            </div>
          </fieldset>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {submitting ? 'Creating your Digital Twin…' : 'Create Digital Twin & Evaluate Compliance'}
          </button>
        </form>
      </main>
    </div>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700">{label}</span>
      {children}
    </label>
  )
}
