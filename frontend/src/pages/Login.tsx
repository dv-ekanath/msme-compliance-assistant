import { useState, type FormEvent, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import { login, register, storeSession } from '../lib/auth'
import type { UserRole } from '../types'

const ROLES: { value: UserRole; label: string }[] = [
  { value: 'owner', label: 'MSME Owner' },
  { value: 'ca', label: 'CA / Reviewer' },
]

export default function Login() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState<UserRole>('owner')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const token = mode === 'login' ? await login(email, password) : await register(email, password, fullName, role)
      storeSession(token)
      const lastBusinessId = localStorage.getItem('lastBusinessId')
      navigate(lastBusinessId ? `/filings/${lastBusinessId}` : '/onboarding')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <Nav />
      <main className="mx-auto max-w-sm px-6 py-10">
        <h1 className="mb-1 text-xl font-semibold">{mode === 'login' ? 'Log in' : 'Create an account'}</h1>
        <p className="mb-6 text-sm text-slate-500">
          {mode === 'login'
            ? 'CA/reviewer accounts can approve, reject, and submit filings.'
            : 'Demo accounts: owner@demo.msme / ca@demo.msme, password demo1234.'}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-6">
          <Field label="Email">
            <input
              required
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input"
              placeholder="owner@demo.msme"
            />
          </Field>
          {mode === 'register' && (
            <>
              <Field label="Full name">
                <input
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="input"
                />
              </Field>
              <Field label="Role">
                <select value={role} onChange={(e) => setRole(e.target.value as UserRole)} className="input">
                  {ROLES.map((r) => (
                    <option key={r.value} value={r.value}>
                      {r.label}
                    </option>
                  ))}
                </select>
              </Field>
            </>
          )}
          <Field label="Password">
            <input
              required
              type="password"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input"
            />
          </Field>

          {error && <p className="text-sm text-red-600">{error}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {submitting ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Register'}
          </button>

          <button
            type="button"
            onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
            className="w-full text-center text-sm text-slate-500 underline"
          >
            {mode === 'login' ? 'Need an account? Register' : 'Already have an account? Log in'}
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
