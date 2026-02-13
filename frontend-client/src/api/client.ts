// SECURITY NOTE (H-6): Tokens are stored in localStorage for this PoC.
// In production, migrate to httpOnly cookies set by the backend to prevent
// XSS-based token theft. See: OWASP Token Storage Cheat Sheet.
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function refreshToken(): Promise<string | null> {
  const refresh = localStorage.getItem('refresh_token')
  if (!refresh) return null

  const res = await fetch(`${API_BASE}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refresh }),
  })

  if (!res.ok) return null

  const data = await res.json()
  localStorage.setItem('token', data.access_token)
  if (data.refresh_token) {
    localStorage.setItem('refresh_token', data.refresh_token)
  }
  return data.access_token
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((options.headers as Record<string, string>) || {}),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers })

  // Attempt token refresh on 401
  if (res.status === 401 && token) {
    const newToken = await refreshToken()
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`
      res = await fetch(`${API_BASE}${path}`, { ...options, headers })
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    const detail = Array.isArray(body.detail)
      ? body.detail.map((e: { msg?: string }) => e.msg).join(', ')
      : body.detail
    throw new ApiError(res.status, detail || res.statusText)
  }

  if (res.status === 204) return undefined as T
  return res.json()
}
