import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import Nav from '../components/Nav'
import { getTwin } from '../lib/api'
import type { DigitalTwin } from '../types'

const HEALTH_STYLES: Record<DigitalTwin['summary']['compliance_health'], string> = {
  good: 'bg-emerald-100 text-emerald-700',
  attention_needed: 'bg-amber-100 text-amber-700',
  critical: 'bg-red-100 text-red-700',
}

const HEALTH_LABELS: Record<DigitalTwin['summary']['compliance_health'], string> = {
  good: 'Good standing',
  attention_needed: 'Needs attention',
  critical: 'Critical',
}

const SECTOR_LABELS: Record<string, string> = {
  trading: 'Trading / Goods',
  manufacturing: 'Manufacturing',
  services: 'Services',
  other: 'Other',
}

const REGISTRATION_LABELS: Record<string, string> = {
  gst: 'GST',
  udyam: 'Udyam',
  shops_establishment: 'Shops & Establishment',
  epf: 'EPF',
  esi: 'ESI',
  professional_tax: 'Professional Tax',
  other: 'Other',
}

export default function Dashboard() {
  const { businessId } = useParams<{ businessId: string }>()
  const [twin, setTwin] = useState<DigitalTwin | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!businessId) return
    getTwin(businessId)
      .then(setTwin)
      .catch(() => setError('Could not load this business. It may not exist yet.'))
  }, [businessId])

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <Nav />
        <main className="mx-auto max-w-5xl px-6 py-10">
          <p className="text-sm text-red-600">{error}</p>
          <Link to="/onboarding" className="mt-4 inline-block text-sm text-slate-600 underline">
            Start onboarding
          </Link>
        </main>
      </div>
    )
  }

  if (!twin) {
    return (
      <div className="min-h-screen bg-slate-50 text-slate-900">
        <Nav />
        <main className="mx-auto max-w-5xl px-6 py-10 text-sm text-slate-500">Loading…</main>
      </div>
    )
  }

  const { business, registrations, summary, upcoming_deadlines: upcomingDeadlines } = twin

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">{business.name}</h1>
            <p className="text-sm text-slate-500">
              {SECTOR_LABELS[business.sector]} · {business.state} · {business.employee_count} employees
            </p>
          </div>
          <span className={`rounded-full px-3 py-1 text-xs font-medium ${HEALTH_STYLES[summary.compliance_health]}`}>
            {HEALTH_LABELS[summary.compliance_health]}
          </span>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-5">
          <StatTile label="Applicable" value={summary.total_applicable} />
          <StatTile label="Completed" value={summary.completed} tone="text-emerald-600" />
          <StatTile label="Due soon" value={summary.due_soon} tone="text-amber-600" />
          <StatTile label="Overdue" value={summary.overdue} tone="text-red-600" />
          <StatTile label="Needs review" value={summary.review_required} tone="text-slate-500" />
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-500">
              Business Profile
            </h2>
            <dl className="space-y-2 text-sm">
              <Row label="Legal structure" value={business.registration_type.replace('_', ' ')} />
              <Row label="Turnover band" value={business.turnover_band} />
              <Row label="Incorporation date" value={business.incorporation_date ?? '—'} />
              <Row label="GSTIN" value={business.gstin ?? '—'} />
              <Row label="PAN" value={business.pan ?? '—'} />
              <Row label="Udyam number" value={business.udyam_number ?? '—'} />
            </dl>
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-500">
              Registrations
            </h2>
            {registrations.length === 0 ? (
              <p className="text-sm text-slate-400">None on file yet.</p>
            ) : (
              <ul className="space-y-2">
                {registrations.map((r) => (
                  <li key={r.id} className="flex items-center justify-between text-sm">
                    <span>{REGISTRATION_LABELS[r.type] ?? r.type}</span>
                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                      {r.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5 md:col-span-2">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-medium uppercase tracking-wide text-slate-500">
                Upcoming Deadlines
              </h2>
              <Link to={`/checklist/${business.id}`} className="text-sm text-slate-600 underline">
                View full checklist
              </Link>
            </div>
            {upcomingDeadlines.length === 0 ? (
              <p className="text-sm text-slate-400">No upcoming deadlines.</p>
            ) : (
              <ul className="divide-y divide-slate-100">
                {upcomingDeadlines.map((o) => (
                  <li key={o.id} className="flex items-center justify-between py-2 text-sm">
                    <span>{o.title}</span>
                    <span className="text-slate-500">{o.due_date}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}

function StatTile({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 text-center">
      <p className={`text-2xl font-semibold ${tone ?? 'text-slate-900'}`}>{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  )
}
