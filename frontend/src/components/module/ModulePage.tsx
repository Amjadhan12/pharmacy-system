import { Construction } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import EmptyState from '@/components/ui/EmptyState'
import Spinner from '@/components/ui/Spinner'
import { apiGet, ApiRequestError } from '@/services/api'
import type { Paginated } from '@/types/api'

interface ModulePageProps {
  title: string
  apiPath?: string
  columns?: { key: string; label: string }[]
}

type ModuleRecord = Record<string, unknown>

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export default function ModulePage({
  title,
  apiPath,
  columns = [],
}: ModulePageProps) {
  const query = useQuery({
    queryKey: ['module-records', apiPath],
    queryFn: () => apiGet<Paginated<ModuleRecord>>(apiPath ?? ''),
    enabled: Boolean(apiPath),
  })

  if (!apiPath) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            This module is not implemented by the current backend.
          </p>
        </div>
        <EmptyState
          icon={<Construction className="h-6 w-6" />}
          title={`${title} is not available yet`}
          description="No demo records or sample values are displayed."
        />
      </div>
    )
  }

  if (query.isLoading) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    )
  }

  if (query.isError) {
    const message =
      query.error instanceof ApiRequestError
        ? query.error.message
        : 'Unable to load records from the API.'
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <div role="alert" className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700 dark:bg-rose-950 dark:text-rose-300">
          {message}
        </div>
      </div>
    )
  }

  const records = query.data?.results ?? []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          {query.data?.count ?? records.length} records available to your account.
        </p>
      </div>

      {records.length === 0 ? (
        <EmptyState
          title={`No ${title.toLowerCase()} found`}
          description="No matching records are currently available for your assigned pharmacy or branches."
        />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <table className="min-w-full divide-y divide-zinc-200 text-left text-sm dark:divide-zinc-800">
            <thead className="bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
              <tr>
                {columns.map((column) => (
                  <th key={column.key} scope="col" className="px-4 py-3 font-medium">
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {records.map((record, index) => (
                <tr key={String(record.id ?? index)}>
                  {columns.map((column) => (
                    <td key={column.key} className="whitespace-nowrap px-4 py-3 text-zinc-700 dark:text-zinc-300">
                      {displayValue(record[column.key])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
