import axios, { AxiosError, type AxiosRequestConfig } from 'axios'
import type { ApiEnvelope } from '@/types/api'

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000/api/v1'

const ACCESS_TOKEN_KEY = 'pharmafin.access'
const REFRESH_TOKEN_KEY = 'pharmafin.refresh'

/** JWT token persistence (localStorage — never expose provider keys here). */
export const tokenStorage = {
  getAccess: (): string | null => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefresh: (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY),
  set(access: string, refresh: string): void {
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  },
  clear(): void {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

/** Normalised error thrown by every API helper. */
export class ApiRequestError extends Error {
  readonly status?: number
  readonly errors: unknown

  constructor(message: string, status?: number, errors?: unknown) {
    super(message)
    this.name = 'ApiRequestError'
    this.status = status
    this.errors = errors
  }
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ success?: boolean; message?: string; errors?: unknown }>) => {
    if (error.response) {
      const { status, data } = error.response
      const message =
        data && typeof data === 'object' && data.message
          ? data.message
          : status >= 500
            ? 'The server encountered an error. Please try again.'
            : 'Request failed. Please check your input and try again.'
      return Promise.reject(
        new ApiRequestError(message, status, data?.errors),
      )
    }
    return Promise.reject(
      new ApiRequestError('Unable to reach the PharmaFin API. Check that the backend is running.'),
    )
  },
)

/** GET helper that unwraps the standard {success, message, data} envelope. */
export async function apiGet<T>(
  path: string,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await api.get<ApiEnvelope<T>>(path, config)
  return response.data.data
}

/** POST helper that unwraps the standard {success, message, data} envelope. */
export async function apiPost<T>(
  path: string,
  body?: unknown,
  config?: AxiosRequestConfig,
): Promise<T> {
  const response = await api.post<ApiEnvelope<T>>(path, body, config)
  return response.data.data
}
