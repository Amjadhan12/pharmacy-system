/** Shared API types matching the Django backend response envelope. */

export interface ApiEnvelope<T> {
  success: boolean
  message: string
  data: T
}

export interface ApiErrorBody {
  success: false
  message: string
  errors: unknown
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface HealthData {
  service: string
  status: 'ok' | 'degraded'
  database: 'ok' | 'unavailable'
  time: string
}

export interface Role {
  id: number
  name: string
  code: string
  description: string
}

export interface User {
  id: number
  email: string
  username: string
  first_name: string
  last_name: string
  full_name: string
  phone: string
  avatar: string | null
  role: Role | null
  is_active: boolean
  date_joined: string
}

export interface TokenPair {
  access: string
  refresh: string
}
