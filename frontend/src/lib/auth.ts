import type { TokenResponse, UserRole } from '../types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const TOKEN_KEY = 'authToken'
const ROLE_KEY = 'authRole'

async function parseTokenResponse(res: Response): Promise<TokenResponse> {
  if (!res.ok) {
    const body = await res.text()
    throw new Error(body || `Request failed: ${res.status}`)
  }
  return res.json() as Promise<TokenResponse>
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return fetch(`${API_BASE_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  }).then(parseTokenResponse)
}

export function register(
  email: string,
  password: string,
  fullName: string,
  role: UserRole,
): Promise<TokenResponse> {
  return fetch(`${API_BASE_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, full_name: fullName, role }),
  }).then(parseTokenResponse)
}

export function storeSession(token: TokenResponse): void {
  localStorage.setItem(TOKEN_KEY, token.access_token)
  localStorage.setItem(ROLE_KEY, token.role)
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(ROLE_KEY)
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getRole(): UserRole | null {
  return localStorage.getItem(ROLE_KEY) as UserRole | null
}

export function isReviewer(): boolean {
  const role = getRole()
  return role === 'ca' || role === 'admin'
}
