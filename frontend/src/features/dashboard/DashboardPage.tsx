import {
  Boxes,
  Building2,
  CircleAlert,
  Pill,
  Timer,
  Truck,
  Users,
} from 'lucide-react'
import Badge from '@/components/ui/Badge'
import Card, { CardHeader } from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Spinner from '@/components/ui/Spinner'
import { useAuth } from '@/features/auth/AuthContext'
import { formatDate } from '@/utils/format'
import StatCard from './StatCard'
import { useDashboardSummary } from './useDashboardSummary'
import { useSystemHealth } from './useSystemHealth'

export default function DashboardPage() {
  const { user } = useAuth()
  const { data: health, isLoading, isError } = useSystemHealth()
  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
  } = useDashboardSummary()

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            {user
              ? `Welcome back, ${user.full_name}.`
              : 'Pharmacy financial overview'}
          </p>
        </div>

        {/* Real, API-connected system status */}
        <div className="flex items-center gap-2 text-sm">
          {isLoading && <Spinner />}
          {isError && (
            <Badge tone="danger">API unreachable</Badge>
          )}
          {health && (
            <>
              <Badge tone={health.status === 'ok' ? 'success' : 'danger'}>
                API {health.status}
              </Badge>
              <Badge tone={health.database === 'ok' ? 'success' : 'danger'}>
                DB {health.database}
              </Badge>
              <span className="hidden text-xs text-zinc-400 sm:inline">
                checked {formatDate(health.time)}
              </span>
            </>
          )}
        </div>
      </div>

      {summaryLoading && (
        <div className="flex min-h-32 items-center justify-center">
          <Spinner className="h-8 w-8" />
        </div>
      )}
      {summaryError && (
        <div
          role="alert"
          className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700 dark:bg-rose-950 dark:text-rose-300"
        >
          Dashboard data could not be loaded from the API.
        </div>
      )}
      {summary && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: 'Medicines', value: summary.medicines, icon: Pill },
            { label: 'Stock units', value: summary.stock_units, icon: Boxes },
            { label: 'Branches', value: summary.branches, icon: Building2 },
            { label: 'Suppliers', value: summary.suppliers, icon: Truck },
            { label: 'Customers', value: summary.customers, icon: Users },
            {
              label: 'Expiring batches',
              value: summary.expiring_batches,
              icon: Timer,
              tone: 'warning' as const,
            },
            {
              label: 'Expired batches',
              value: summary.expired_batches,
              icon: CircleAlert,
              tone: 'warning' as const,
            },
            { label: 'All batches', value: summary.batches, icon: Boxes },
          ].map((metric) => (
            <StatCard
              key={metric.label}
              label={metric.label}
              value={metric.value.toLocaleString()}
              icon={metric.icon}
              tone={metric.tone}
            />
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="Revenue & profit trend"
            subtitle="Daily revenue, expenses and net profit"
          />
          <div className="p-5">
            <EmptyState
              title="Sales and profit trends are unavailable"
              description="The backend does not currently implement sales or expense transaction APIs. This dashboard does not fabricate financial figures."
            />
          </div>
        </Card>

        <Card>
          <CardHeader
            title="Branch performance"
            subtitle="Sales and margins by branch"
          />
          <div className="p-5">
            <EmptyState
              title={`${summary?.branches ?? 0} accessible branches`}
              description="Branch sales comparisons require sales transactions, which are not implemented in the current backend."
            />
          </div>
        </Card>
      </div>
    </div>
  )
}
