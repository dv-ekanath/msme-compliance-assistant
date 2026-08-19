import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import Nav from '../components/Nav'
import { acknowledgeAlert, listAlerts } from '../lib/api'
import type { Alert, AlertSeverity } from '../types'

const SEVERITY_STYLES: Record<AlertSeverity, string> = {
  low: 'bg-slate-100 text-slate-600',
  medium: 'bg-amber-100 text-amber-700',
  high: 'bg-red-100 text-red-700',
}

const TYPE_LABELS: Record<Alert['alert_type'], string> = {
  regulation_change: 'Regulation change',
  growth_forecast: 'Growth forecast',
}

export default function Alerts() {
  const { businessId } = useParams<{ businessId: string }>()
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!businessId) return
    listAlerts(businessId)
      .then(setAlerts)
      .finally(() => setLoading(false))
  }, [businessId])

  async function acknowledge(alert: Alert) {
    const updated = await acknowledgeAlert(alert.id)
    setAlerts((prev) => prev.map((a) => (a.id === updated.id ? updated : a)))
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-1 text-xl font-semibold">Alerts</h1>
        <p className="mb-6 text-sm text-slate-500">
          Regulation-change alerts come from the watchdog scan of each regulation's official
          source; growth-forecast alerts predict an obligation before it becomes applicable,
          based on your current employee count. Both are deterministic -- no LLM decides these.
        </p>

        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : alerts.length === 0 ? (
          <p className="text-sm text-slate-400">No alerts right now.</p>
        ) : (
          <ul className="space-y-3">
            {alerts.map((a) => (
              <li key={a.id} className="rounded-lg border border-slate-200 bg-white p-5">
                <div className="mb-2 flex items-start justify-between gap-4">
                  <div>
                    <p className="font-medium">{a.title}</p>
                    <p className="text-xs text-slate-400">{TYPE_LABELS[a.alert_type]}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${SEVERITY_STYLES[a.severity]}`}
                    >
                      {a.severity}
                    </span>
                    {a.acknowledged_at && (
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                        Acknowledged
                      </span>
                    )}
                  </div>
                </div>

                <p className="mb-3 text-sm text-slate-600">{a.message}</p>

                {a.regulation_source_url && (
                  <p className="mb-3 text-xs text-slate-400">
                    Source:{' '}
                    <a
                      href={a.regulation_source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="underline hover:text-slate-600"
                    >
                      {a.regulation_title}
                    </a>
                  </p>
                )}

                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Detected: {new Date(a.detected_at).toLocaleString()}</span>
                  {!a.acknowledged_at && (
                    <button
                      onClick={() => acknowledge(a)}
                      className="rounded-md border border-slate-300 px-2 py-1 text-slate-600 hover:bg-slate-50"
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  )
}
