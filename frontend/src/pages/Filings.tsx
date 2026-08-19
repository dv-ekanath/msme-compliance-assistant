import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import Nav from '../components/Nav'
import { approveFiling, listFilings, rejectFiling, submitFiling } from '../lib/api'
import { getToken, isReviewer } from '../lib/auth'
import type { Filing, FilingStatus } from '../types'

const STATUS_STYLES: Record<FilingStatus, string> = {
  draft: 'bg-slate-100 text-slate-600',
  approved: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-red-100 text-red-700',
  submitted: 'bg-blue-100 text-blue-700',
}

export default function Filings() {
  const { businessId } = useParams<{ businessId: string }>()
  const [filings, setFilings] = useState<Filing[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const reviewer = isReviewer()
  const loggedIn = getToken() !== null

  useEffect(() => {
    if (!businessId) return
    listFilings(businessId)
      .then(setFilings)
      .finally(() => setLoading(false))
  }, [businessId])

  async function act(filing: Filing, action: (id: string) => Promise<Filing>) {
    setError(null)
    try {
      const updated = await action(filing.id)
      setFilings((prev) => prev.map((f) => (f.id === updated.id ? updated : f)))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not update this filing.')
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Nav />
      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="mb-1 text-xl font-semibold">Filings</h1>
        <p className="mb-6 text-sm text-slate-500">
          Every draft is generated deterministically from the Digital Twin -- no AI decides its
          content. A CA/reviewer must approve before submission, and submission is always a
          simulated mock, never a real government portal filing.
        </p>

        {!loggedIn && (
          <p className="mb-6 text-sm text-amber-700">
            You're not logged in -- filings are visible, but approving, rejecting, or submitting
            requires a CA/reviewer account.
          </p>
        )}

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        {loading ? (
          <p className="text-sm text-slate-500">Loading…</p>
        ) : filings.length === 0 ? (
          <p className="text-sm text-slate-400">
            No filings yet -- prepare one from an applicable filing obligation on the Checklist.
          </p>
        ) : (
          <ul className="space-y-3">
            {filings.map((f) => (
              <li key={f.id} className="rounded-lg border border-slate-200 bg-white p-5">
                <div className="mb-2 flex items-start justify-between gap-4">
                  <div>
                    <p className="font-medium">{f.obligation_title}</p>
                    <p className="text-xs text-slate-400">{f.period ?? 'Current period'}</p>
                  </div>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLES[f.status]}`}>
                    {f.status}
                  </span>
                </div>

                <pre className="mb-3 whitespace-pre-wrap rounded-md bg-slate-50 p-3 text-xs text-slate-600">
                  {f.document_ref}
                </pre>

                {f.status === 'submitted' && f.mock_notice && (
                  <div className="mb-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                    {f.mock_notice}
                  </div>
                )}

                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>Prepared: {new Date(f.created_at).toLocaleString()}</span>
                  {reviewer && f.status === 'draft' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => act(f, rejectFiling)}
                        className="rounded-md border border-red-200 px-2 py-1 text-red-600 hover:bg-red-50"
                      >
                        Reject
                      </button>
                      <button
                        onClick={() => act(f, approveFiling)}
                        className="rounded-md border border-emerald-200 px-2 py-1 text-emerald-700 hover:bg-emerald-50"
                      >
                        Approve
                      </button>
                    </div>
                  )}
                  {reviewer && f.status === 'approved' && (
                    <button
                      onClick={() => act(f, submitFiling)}
                      className="rounded-md bg-slate-900 px-3 py-1 text-white hover:bg-slate-700"
                    >
                      Submit (mock)
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
