import { Link, useParams } from 'react-router-dom'

export default function Nav() {
  const { businessId } = useParams<{ businessId?: string }>()

  return (
    <header className="border-b border-slate-200 bg-white px-6 py-4">
      <div className="mx-auto flex max-w-5xl items-center justify-between">
        <div>
          <Link to="/" className="text-lg font-semibold hover:underline">
            MSME Compliance Assistant
          </Link>
          <p className="text-sm text-slate-500">Compliance Digital Twin — SIH 2026</p>
        </div>
        <nav className="flex items-center gap-4 text-sm font-medium">
          {businessId && (
            <>
              <Link to={`/dashboard/${businessId}`} className="text-slate-600 hover:text-slate-900">
                Dashboard
              </Link>
              <Link to={`/checklist/${businessId}`} className="text-slate-600 hover:text-slate-900">
                Checklist
              </Link>
            </>
          )}
          <Link
            to="/onboarding"
            className="rounded-md bg-slate-900 px-3 py-1.5 text-white hover:bg-slate-700"
          >
            {businessId ? 'New Business' : 'Get Started'}
          </Link>
        </nav>
      </div>
    </header>
  )
}
