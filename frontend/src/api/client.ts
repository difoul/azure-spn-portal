import { msalInstance, loginRequest } from '../auth/msalConfig'
import type { ApiError } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string
const IS_MOCK = import.meta.env.VITE_ENABLE_MOCK === 'true'

async function getAccessToken(): Promise<string> {
  if (IS_MOCK) return 'mock-token'

  const accounts = msalInstance.getAllAccounts()
  if (accounts.length === 0) {
    throw new Error('No authenticated account found')
  }

  try {
    const response = await msalInstance.acquireTokenSilent({
      ...loginRequest,
      account: accounts[0],
    })
    return response.accessToken
  } catch {
    // Silent acquisition failed — fall back to redirect
    await msalInstance.acquireTokenRedirect(loginRequest)
    throw new Error('Redirecting for authentication...')
  }
}

export class ApiRequestError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(`API error ${status}: ${detail}`)
    this.status = status
    this.detail = detail
  }
}

export async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = await getAccessToken()

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...options?.headers,
    },
  })

  if (response.status === 204) {
    return undefined as T
  }

  const data = await response.json().catch(() => ({ detail: response.statusText }))

  if (!response.ok) {
    const err = data as ApiError
    throw new ApiRequestError(response.status, err.detail ?? response.statusText)
  }

  return data as T
}
