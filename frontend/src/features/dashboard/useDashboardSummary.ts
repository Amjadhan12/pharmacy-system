import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/services/api'

export interface DashboardSummary {
  pharmacies: number
  branches: number
  medicines: number
  batches: number
  stock_units: number
  expired_batches: number
  expiring_batches: number
  suppliers: number
  customers: number
}

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => apiGet<DashboardSummary>('/dashboard/summary/'),
    retry: 1,
  })
}
