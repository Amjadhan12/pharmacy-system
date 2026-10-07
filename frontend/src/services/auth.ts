import { apiGet, apiPost, tokenStorage } from '@/services/api'
import type { TokenPair, User } from '@/types/api'

/** Authenticate with the Django backend using email + password (JWT). */
export async function login(email: string, password: string): Promise<void> {
  const tokens = await apiPost<TokenPair>('/auth/token/', { email, password })
  tokenStorage.set(tokens.access, tokens.refresh)
}

/** Fetch the profile for the stored access token. */
export function fetchMe(): Promise<User> {
  return apiGet<User>('/auth/me/')
}

export function logout(): void {
  tokenStorage.clear()
}

export function hasStoredSession(): boolean {
  return Boolean(tokenStorage.getAccess())
}
