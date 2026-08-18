import { useEffect, useState } from 'react'
import { getBackendHealth } from '../lib/api'

const UPCOMING_MODULES = [
  { name: 'Digital Twin', phase: 'Phase 1' },
  { name: 'Compliance Checklist', phase: 'Phase 1' },
  { name: 'RAG-Grounded Q&A', phase: 'Phase 2' },
  { name: 'Predictive Risk', phase: 'Phase 3' },
  { name: 'Regulation Watchdog', phase: 'Phase 3' },
  { name: 'Voice / Vernacular', phase: 'Phase 4' },
  { name: 'Approval Queue', phase: 'Phase 5' },
  { name: 'Audit Trail', phase: 'Phase 5' },
]

type BackendStatus = 'checking' | 'online' | 'offline'

export default function Dashboard() {
  const [status, setStatus] = useState<BackendStatus>('checking')

  useEffect(() => {
    getBackendHealth()
      .then(() => setStatus('online'))
      .catch(() => setStatus('offline'))
  }, [])

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">MSME Compliance Assistant</h1>
            <p className="text-sm text-slate-500">Compliance Digital Twin — SIH 2026</p>
          </div>
          <StatusBadge status={status} />
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="mb-8 rounded-lg border border-slate-200 bg-white p-6">
          <h2 className="mb-1 text-base font-medium">Phase 0 — Foundation</h2>
          <p className="text-sm text-slate-500">
            Repo scaffold, backend/frontend skeletons, and database configuration are in
            place. Feature modules below will be built out in later phases.
          </p>
        </div>

        <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-500">
          Planned Modules
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
          {UPCOMING_MODULES.map((m) => (
            <div
              key={m.name}
              className="rounded-lg border border-dashed border-slate-300 bg-white p-4 opacity-70"
            >
              <p className="font-medium">{m.name}</p>
              <p className="text-xs text-slate-400">{m.phase}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

function StatusBadge({ status }: { status: BackendStatus }) {
  const styles: Record<BackendStatus, string> = {
    checking: 'bg-slate-100 text-slate-600',
    online: 'bg-emerald-100 text-emerald-700',
    offline: 'bg-red-100 text-red-700',
  }
  const label: Record<BackendStatus, string> = {
    checking: 'Checking backend…',
    online: 'Backend online',
    offline: 'Backend offline',
  }
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-medium ${styles[status]}`}>
      {label[status]}
    </span>
  )
}
