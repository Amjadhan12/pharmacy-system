import {
  Boxes,
  Landmark,
  Receipt,
  ShoppingCart,
  Timer,
  TrendingUp,
  Truck,
  Wallet,
} from 'lucide-react'
import Badge from '@/components/ui/Badge'
import Card, { CardHeader } from '@/components/ui/Card'
import EmptyState from '@/components/ui/EmptyState'
import Spinner from '@/components/ui/Spinner'
import { useAuth } from '@/features/auth/AuthContext'
import { formatDate } from '@/utils/format'
import StatCard from './StatCard'
import { useSystemHealth } from './useSystemHealth'

const metrics = [
  { label: 'Sales', icon: ShoppingCart, hint: 'From POS (sales module)' },
  { label: 'Gross Profit', icon: TrendingUp, hint: 'Revenue − COGS' },
  { label: 'Net Profit', icon: Landmark, hint: 'After expenses & tax' },
  { label: 'Cash', icon: Wallet, hint: 'Cash & bank balances' },
  { label: 'Receivable', icon: Truck, hint: 'Customer credit outstanding' },
  { label: 'Payable', icon: Receipt, hint: 'Supplier dues' },
  { label: 'Inventory Value', icon: Boxes, hint: 'At purchase cost' },
  { label: 'Expiring Stock', icon: Timer, hint: 'Within 90 days', tone: 'warning' as const },
]

export default function DashboardPage() {
  const { user } = useAuth()
  const { data: health, isLoading, isError } = useSystemHealth()

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

      {/* KPI cards — real values appear as modules come online */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <StatCard
            key={metric.label}
            label={metric.label}
            value={null}
            hint={metric.hint}
            icon={metric.icon}
            tone={metric.tone}
          />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader
            title="Revenue & profit trend"
            subtitle="Daily revenue, expenses and net profit"
          />
          <div className="p-5">
            <EmptyState
              title="Charts start when data exists"
              description="Revenue, expense and profit series will be rendered from /api/v1/reports/ after sales and accounting go live. No fabricated samples are shown."
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
              title="No branch data yet"
              description="Branch comparisons will populate from live sales data once branches record transactions."
            />
          </div>
        </Card>
      </div>
    </div>
  )
}
