import { Link, useNavigate, useParams } from 'react-router-dom'
import { clearSession, getRole, getToken } from '../lib/auth'

export default function Nav() {
  const { businessId } = useParams<{ businessId?: string }>()
  const navigate = useNavigate()
  const token = getToken()
  const role = getRole()

  function logout() {
    clearSession()
    navigate('/login')
  }

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
              <Link to={`/copilot/${businessId}`} className="text-slate-600 hover:text-slate-900">
                Copilot
              </Link>
              <Link to={`/alerts/${businessId}`} className="text-slate-600 hover:text-slate-900">
                Alerts
              </Link>
              <Link to={`/filings/${businessId}`} className="text-slate-600 hover:text-slate-900">
                Filings
              </Link>
            </>
          )}
          <Link
            to="/onboarding"
            className="rounded-md bg-slate-900 px-3 py-1.5 text-white hover:bg-slate-700"
          >
            {businessId ? 'New Business' : 'Get Started'}
          </Link>
          {token ? (
            <button onClick={logout} className="text-slate-600 hover:text-slate-900">
              Log out ({role})
            </button>
          ) : (
            <Link to="/login" className="text-slate-600 hover:text-slate-900">
              Log in
            </Link>
          )}
        </nav>
      </div>
    </header>
  )
}
