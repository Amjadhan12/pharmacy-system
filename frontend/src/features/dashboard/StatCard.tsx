import type { LucideIcon } from 'lucide-react'
import Card from '@/components/ui/Card'
import { cn } from '@/lib/utils'

interface StatCardProps {
  label: string
  value: string | null | undefined
  hint?: string
  icon: LucideIcon
  tone?: 'default' | 'success' | 'warning'
}

/** Dashboard metric card — renders "—" until real module data exists. */
export default function StatCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = 'default',
}: StatCardProps) {
  return (
    <Card className="p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            {label}
          </p>
          <p className="mt-2 text-2xl font-semibold tabular-nums text-zinc-900 dark:text-zinc-50">
            {value ?? '—'}
          </p>
          {hint && (
            <p className="mt-1.5 text-xs text-zinc-400 dark:text-zinc-500">
              {hint}
            </p>
          )}
        </div>
        <div
          className={cn(
            'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg',
            tone === 'success' &&
              'bg-emerald-50 text-emerald-600 dark:bg-emerald-950 dark:text-emerald-400',
            tone === 'warning' &&
              'bg-amber-50 text-amber-600 dark:bg-amber-950 dark:text-amber-400',
            tone === 'default' &&
              'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400',
          )}
        >
          <Icon className="h-4.5 w-4.5" aria-hidden />
        </div>
      </div>
    </Card>
  )
}
