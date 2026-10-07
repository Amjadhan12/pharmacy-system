import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useMemo, useState, type FormEvent } from 'react'
import EmptyState from '@/components/ui/EmptyState'
import Spinner from '@/components/ui/Spinner'
import { useAuth } from '@/features/auth/AuthContext'
import { api, ApiRequestError } from '@/services/api'
import type { ApiEnvelope, Paginated } from '@/types/api'

type Row = Record<string, unknown>
type FieldType = 'text' | 'email' | 'number' | 'textarea' | 'checkbox' | 'select'

export interface DataModuleField {
  key: string
  label: string
  type?: FieldType
  required?: boolean
  choices?: { value: string | number; label: string }[]
  lookup?: string
}

interface DataModulePageProps {
  title: string
  apiPath: string
  columns: { key: string; label: string }[]
  fields: DataModuleField[]
  canWriteRoles?: string[]
}

function getRows(data: Paginated<Row> | undefined): Row[] {
  return data?.results ?? []
}

function showValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export default function DataModulePage({
  title,
  apiPath,
  columns,
  fields,
  canWriteRoles = [],
}: DataModulePageProps) {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState<Row | null>(null)
  const [creating, setCreating] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const canWrite =
    Boolean(user?.is_active) &&
    (Boolean(user?.role?.code && canWriteRoles.includes(user.role.code)) ||
      user?.role?.code === 'super_admin')

  const listQuery = useQuery({
    queryKey: ['module-records', apiPath, search, page],
    queryFn: async () => {
      const response = await api.get<ApiEnvelope<Paginated<Row>>>(apiPath, {
        params: { search: search || undefined, page },
      })
      return response.data.data
    },
  })

  const lookupPaths = useMemo(
    () => [...new Set(fields.flatMap((field) => field.lookup ? [field.lookup] : []))],
    [fields],
  )
  const lookups = useQuery({
    queryKey: ['module-lookups', lookupPaths],
    enabled: lookupPaths.length > 0,
    queryFn: async () => {
      const pairs = await Promise.all(
        lookupPaths.map(async (path) => {
          const response = await api.get<ApiEnvelope<Paginated<Row>>>(path)
          return [path, response.data.data.results] as const
        }),
      )
      return Object.fromEntries(pairs) as Record<string, Row[]>
    },
  })

  const saveMutation = useMutation({
    mutationFn: async (values: Row) => {
      if (editing?.id) {
        return api.patch(`${apiPath}${editing.id}/`, values)
      }
      return api.post(apiPath, values)
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['module-records', apiPath] })
      setCreating(false)
      setEditing(null)
      setFormError(null)
    },
    onError: (error) => {
      setFormError(
        error instanceof ApiRequestError
          ? error.message
          : 'Unable to save this record.',
      )
    },
  })

  const deactivateMutation = useMutation({
    mutationFn: (id: unknown) => api.delete(`${apiPath}${String(id)}/`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['module-records', apiPath] }),
  })

  function startCreate() {
    setEditing(null)
    setFormError(null)
    setCreating(true)
  }

  function startEdit(row: Row) {
    setCreating(false)
    setFormError(null)
    setEditing(row)
  }

  function submitForm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const values: Row = {}

    for (const field of fields) {
      if (field.key === 'pharmacy') {
        const value = form.get(field.key)
        values[field.key] = value ? Number(value) : user?.pharmacies[0]?.id
      } else if (field.type === 'checkbox') {
        values[field.key] = form.get(field.key) === 'on'
      } else if (field.type === 'number') {
        const value = form.get(field.key)
        if (value !== null && value !== '') values[field.key] = Number(value)
      } else if (field.type === 'select') {
        const value = form.get(field.key)
        if (value) {
          values[field.key] = field.lookup ? Number(value) : String(value)
        } else if (field.lookup && !field.required) {
          values[field.key] = null
        }
      } else {
        const value = form.get(field.key)
        values[field.key] = value === null ? '' : String(value)
      }
    }

    setFormError(null)
    saveMutation.mutate(values)
  }

  const data = listQuery.data
  const rows = getRows(data)
  const isFormOpen = creating || editing !== null
  const totalPages = data ? Math.max(1, Math.ceil(data.count / 20)) : 1

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            {data ? `${data.count} records in your accessible pharmacy.` : 'Records from your accessible pharmacy.'}
          </p>
        </div>
        <div className="flex gap-2">
          <input
            aria-label={`Search ${title.toLowerCase()}`}
            className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
            placeholder="Search"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value)
              setPage(1)
            }}
          />
          {canWrite && (
            <button
              type="button"
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
              onClick={startCreate}
            >
              Add {title.replace(/s$/, '')}
            </button>
          )}
        </div>
      </div>

      {isFormOpen && (
        <form
          className="grid gap-4 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm dark:border-zinc-800 dark:bg-zinc-900 sm:grid-cols-2"
          onSubmit={submitForm}
        >
          <h2 className="text-base font-semibold sm:col-span-2">
            {editing ? `Edit ${title.replace(/s$/, '')}` : `Add ${title.replace(/s$/, '')}`}
          </h2>
          {fields.filter((field) => field.key !== 'pharmacy').map((field) => {
            const initial = editing?.[field.key]
            const fieldType = field.type ?? 'text'
            const options = field.lookup ? lookups.data?.[field.lookup] ?? [] : []
            const common = {
              id: field.key,
              name: field.key,
              required: field.required,
              defaultValue: fieldType === 'checkbox' ? undefined : showValue(initial) === '—' ? '' : showValue(initial),
              className: 'w-full rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-950',
            }

            if (fieldType === 'checkbox') {
              return (
                <label key={field.key} className="flex items-center gap-2 text-sm">
                  <input
                    id={field.key}
                    name={field.key}
                    type="checkbox"
                    defaultChecked={initial === undefined ? true : Boolean(initial)}
                    className="h-4 w-4 rounded border-zinc-300 text-emerald-600"
                  />
                  {field.label}
                </label>
              )
            }

            return (
              <label key={field.key} htmlFor={field.key} className="space-y-1 text-sm">
                <span className="font-medium">{field.label}</span>
                {fieldType === 'textarea' ? (
                  <textarea {...common} rows={3} />
                ) : fieldType === 'select' ? (
                  <select {...common} defaultValue={initial === undefined ? '' : String(initial)}>
                    <option value="">Select {field.label.toLowerCase()}</option>
                    {field.choices?.map((choice) => (
                      <option key={choice.value} value={choice.value}>{choice.label}</option>
                    ))}
                    {options.map((option) => (
                      <option key={String(option.id)} value={String(option.id)}>
                        {String(option.name ?? option.code ?? option.id)}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input {...common} type={fieldType} />
                )}
              </label>
            )
          })}
          {formError && (
            <p role="alert" className="text-sm text-rose-600 sm:col-span-2">{formError}</p>
          )}
          <div className="flex gap-2 sm:col-span-2">
            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
            >
              {saveMutation.isPending ? 'Saving…' : 'Save'}
            </button>
            <button
              type="button"
              className="rounded-lg border border-zinc-300 px-4 py-2 text-sm dark:border-zinc-700"
              onClick={() => {
                setCreating(false)
                setEditing(null)
                setFormError(null)
              }}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {listQuery.isLoading && <div className="flex min-h-40 items-center justify-center"><Spinner className="h-8 w-8" /></div>}
      {listQuery.isError && (
        <div role="alert" className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700 dark:bg-rose-950 dark:text-rose-300">
          {listQuery.error instanceof ApiRequestError ? listQuery.error.message : 'Unable to load records.'}
        </div>
      )}
      {data && rows.length === 0 && (
        <EmptyState title={`No ${title.toLowerCase()} found`} description="No records match your search in the accessible pharmacy." />
      )}
      {rows.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-900">
          <table className="min-w-full divide-y divide-zinc-200 text-left text-sm dark:divide-zinc-800">
            <thead className="bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500 dark:bg-zinc-950 dark:text-zinc-400">
              <tr>
                {columns.map((column) => <th key={column.key} scope="col" className="px-4 py-3 font-medium">{column.label}</th>)}
                {canWrite && <th className="px-4 py-3 font-medium">Actions</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
              {rows.map((row) => (
                <tr key={String(row.id)}>
                  {columns.map((column) => (
                    <td key={column.key} className="whitespace-nowrap px-4 py-3 text-zinc-700 dark:text-zinc-300">
                      {(() => {
                        const field = fields.find((candidate) => candidate.key === column.key)
                        const option = field?.lookup
                          ? lookups.data?.[field.lookup]?.find(
                              (candidate) => String(candidate.id) === String(row[column.key]),
                            )
                          : undefined
                        return showValue(option?.name ?? row[column.key])
                      })()}
                    </td>
                  ))}
                  {canWrite && (
                    <td className="whitespace-nowrap px-4 py-3">
                      <button type="button" className="mr-3 text-emerald-700 hover:underline dark:text-emerald-400" onClick={() => startEdit(row)}>Edit</button>
                      <button
                        type="button"
                        disabled={deactivateMutation.isPending}
                        className="text-rose-700 hover:underline disabled:opacity-50 dark:text-rose-400"
                        onClick={() => {
                          if (window.confirm(`Deactivate this ${title.replace(/s$/, '').toLowerCase()}?`)) {
                            deactivateMutation.mutate(row.id)
                          }
                        }}
                      >
                        Deactivate
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex items-center justify-between border-t border-zinc-200 px-4 py-3 text-sm dark:border-zinc-800">
            <span>Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button type="button" disabled={page <= 1} onClick={() => setPage((value) => value - 1)} className="rounded border px-3 py-1 disabled:opacity-40">Previous</button>
              <button type="button" disabled={page >= totalPages} onClick={() => setPage((value) => value + 1)} className="rounded border px-3 py-1 disabled:opacity-40">Next</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
