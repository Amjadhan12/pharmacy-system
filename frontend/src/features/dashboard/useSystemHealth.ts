import { useQuery } from '@tanstack/react-query'
import { apiGet } from '@/services/api'
import type { HealthData } from '@/types/api'

/** Live backend health probe (API + database connectivity). */
export function useSystemHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => apiGet<HealthData>('/health/'),
    refetchInterval: 30_000,
    retry: 1,
  })
}
