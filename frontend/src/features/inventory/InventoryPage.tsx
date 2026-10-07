import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import Badge from '@/components/ui/Badge'
import EmptyState from '@/components/ui/EmptyState'
import Spinner from '@/components/ui/Spinner'
import { useAuth } from '@/features/auth/AuthContext'
import { apiGet, apiPost, ApiRequestError } from '@/services/api'
import type { Paginated } from '@/types/api'
import { formatCurrency, formatNumber } from '@/utils/format'
import { normalizeDigits } from '@/utils/normalizeDigits'

interface InventoryBatch {
  id: number
  medicine: number
  medicine_name: string
  branch: number
  branch_name: string
  warehouse: number | null
  warehouse_name: string | null
  batch_number: string
  purchase_price: string
  selling_price: string
  quantity: number
  manufacture_date: string | null
  expiry_date: string
  status: string
}

interface InventoryTransaction {
  id: number
  transaction_type: string
  direction: 'in' | 'out'
  batch_number: string
  medicine_name: string
  branch_name: string
  quantity: number
  unit_price: string
  reference: string
  notes: string
  created_at: string
}

interface Lookup {
  id: number
  name?: string
  generic_name?: string
  brand_name?: string
}

const movementTypes = [
  ['purchase', 'Purchase / stock in'],
  ['sale', 'Sale / stock out'],
  ['sale_return', 'Sale return'],
  ['purchase_return', 'Purchase return'],
  ['adjustment_in', 'Adjustment in'],
  ['adjustment_out', 'Adjustment out'],
  ['damage', 'Damaged stock'],
  ['expired', 'Remove expired stock'],
] as const

function requestError(error: unknown, fallback: string): string {
  return error instanceof ApiRequestError ? error.message : fallback
}

function statusTone(status: string): 'success' | 'warning' | 'danger' | 'neutral' {
  if (status === 'available') return 'success'
  if (status === 'expiring') return 'warning'
  if (status === 'expired' || status === 'damaged' || status === 'recalled') {
    return 'danger'
  }
  return 'neutral'
}

export default function InventoryPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [branch, setBranch] = useState('')
  const [warehouse, setWarehouse] = useState('')
  const [category, setCategory] = useState('')
  const [medicine, setMedicine] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [movementType, setMovementType] =
    useState<(typeof movementTypes)[number][0]>('adjustment_in')
  const [batchId, setBatchId] = useState('')
  const [quantity, setQuantity] = useState('')
  const [reference, setReference] = useState('')
  const [notes, setNotes] = useState('')
  const [movementFormError, setMovementFormError] = useState('')
  const [sourceBatch, setSourceBatch] = useState('')
  const [destinationBatch, setDestinationBatch] = useState('')
  const [transferQuantity, setTransferQuantity] = useState('')
  const [transferError, setTransferError] = useState('')
  const canWrite = [
    'super_admin',
    'pharmacy_owner',
    'pharmacy_manager',
    'pharmacist',
    'inventory_manager',
  ].includes(user?.role?.code ?? '')

  const batchesQuery = useQuery({
    queryKey: ['inventory', search, branch, warehouse, category, medicine, status, page],
    queryFn: () =>
      apiGet<Paginated<InventoryBatch>>('/inventory/', {
        params: {
          search: search || undefined,
          branch: branch || undefined,
          warehouse: warehouse || undefined,
          category: category || undefined,
          medicine: medicine || undefined,
          status: status || undefined,
          low_stock: status === 'low_stock' ? 'true' : undefined,
          page,
        },
      }),
  })
  const transactionsQuery = useQuery({
    queryKey: ['inventory-transactions', branch],
    queryFn: () =>
      apiGet<Paginated<InventoryTransaction>>('/inventory/transactions/', {
        params: { branch: branch || undefined, page: 1 },
      }),
  })
  const lookupsQuery = useQuery({
    queryKey: ['inventory-lookups', branch],
    queryFn: async () => {
      const [warehouses, categories, medicines, lowStock, expiring, expired] =
        await Promise.all([
          apiGet<Paginated<Lookup>>('/branches/warehouses/', {
            params: { branch: branch || undefined },
          }),
          apiGet<Paginated<Lookup>>('/medicines/categories/', {
            params: { is_active: 'true' },
          }),
          apiGet<Paginated<Lookup>>('/medicines/medicines/', {
            params: { page_size: 100 },
          }),
          apiGet<Paginated<Lookup>>('/inventory/low-stock/'),
          apiGet<Paginated<InventoryBatch>>('/inventory/expiring/', {
            params: { days: 30 },
          }),
          apiGet<Paginated<InventoryBatch>>('/inventory/expired/'),
        ])
      return { warehouses, categories, medicines, lowStock, expiring, expired }
    },
  })

  const movementMutation = useMutation({
    mutationFn: () =>
      apiPost('/inventory/transactions/stock/' + movementType + '/', {
        batch: Number(batchId),
        quantity: Number(normalizeDigits(quantity)),
        reference,
        notes,
      }),
    onSuccess: async () => {
      setQuantity('')
      setReference('')
      setNotes('')
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['inventory'] }),
        queryClient.invalidateQueries({ queryKey: ['inventory-transactions'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard', 'summary'] }),
      ])
    },
  })
  const transferMutation = useMutation({
    mutationFn: () =>
      apiPost('/inventory/transfers/', {
        source_batch: Number(sourceBatch),
        destination_batch: Number(destinationBatch),
        quantity: Number(normalizeDigits(transferQuantity)),
      }),
    onSuccess: async () => {
      setTransferQuantity('')
      setTransferError('')
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['inventory'] }),
        queryClient.invalidateQueries({ queryKey: ['inventory-transactions'] }),
        queryClient.invalidateQueries({ queryKey: ['dashboard', 'summary'] }),
      ])
    },
    onError: (error) => setTransferError(requestError(error, 'Unable to transfer stock.')),
  })

  const results = batchesQuery.data?.results ?? []
  const totalPages = Math.max(1, Math.ceil((batchesQuery.data?.count ?? 0) / 20))
  const lookupData = lookupsQuery.data
  const submitMovement = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const normalizedQuantity = normalizeDigits(quantity)
    if (!batchId || !/^[1-9]\d*$/.test(normalizedQuantity)) {
      setMovementFormError('Select a batch and enter a positive whole quantity.')
      return
    }
    setMovementFormError('')
    movementMutation.mutate()
  }
  const submitTransfer = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const normalizedQuantity = normalizeDigits(transferQuantity)
    if (
      !sourceBatch
      || !destinationBatch
      || !/^[1-9]\d*$/.test(normalizedQuantity)
    ) {
      setTransferError('Select two batches and enter a positive whole quantity.')
      return
    }
    transferMutation.mutate()
  }

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Inventory</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Branch-scoped batch stock, expiry status, and immutable movement history.
        </p>
      </header>

      {lookupsQuery.isLoading ? (
        <div className="flex min-h-20 items-center justify-center"><Spinner /></div>
      ) : lookupsQuery.isError ? (
        <p role="alert" className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">
          {requestError(lookupsQuery.error, 'Inventory summaries could not be loaded.')}
        </p>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[
            ['Low-stock medicines', lookupData?.lowStock.count ?? 0, 'warning'],
            ['Expiring within 30 days', lookupData?.expiring.count ?? 0, 'warning'],
            ['Expired stock batches', lookupData?.expired.count ?? 0, 'danger'],
            ['Accessible branches', user?.branches.length ?? 0, 'neutral'],
          ].map(([label, value, tone]) => (
            <div key={String(label)} className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
              <p className="text-sm text-zinc-500">{label}</p>
              <p className="mt-2 text-2xl font-semibold">{formatNumber(Number(value))}</p>
              <Badge tone={tone as 'warning' | 'danger' | 'neutral'}>
                Database value
              </Badge>
            </div>
          ))}
        </div>
      )}

      <section className="space-y-4 rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="flex flex-wrap gap-3">
          <input
            aria-label="Search inventory"
            className="min-w-48 flex-1 rounded-lg border border-zinc-300 bg-transparent px-3 py-2 text-sm"
            placeholder="Search medicine, batch or barcode"
            value={search}
            onChange={(event) => { setSearch(event.target.value); setPage(1) }}
          />
          <select aria-label="Branch filter" value={branch} onChange={(event) => { setBranch(event.target.value); setWarehouse(''); setPage(1) }} className="rounded-lg border bg-transparent px-3 py-2 text-sm">
            <option value="">All accessible branches</option>
            {user?.branches.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
          <select aria-label="Warehouse filter" value={warehouse} onChange={(event) => { setWarehouse(event.target.value); setPage(1) }} className="rounded-lg border bg-transparent px-3 py-2 text-sm">
            <option value="">All warehouses</option>
            {lookupData?.warehouses.results.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
          <select aria-label="Category filter" value={category} onChange={(event) => { setCategory(event.target.value); setPage(1) }} className="rounded-lg border bg-transparent px-3 py-2 text-sm">
            <option value="">All categories</option>
            {lookupData?.categories.results.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
          <select aria-label="Medicine filter" value={medicine} onChange={(event) => { setMedicine(event.target.value); setPage(1) }} className="rounded-lg border bg-transparent px-3 py-2 text-sm">
            <option value="">All medicines</option>
            {lookupData?.medicines.results.map((item) => <option key={item.id} value={item.id}>{item.brand_name ? `${item.generic_name} (${item.brand_name})` : item.generic_name ?? item.name ?? item.id}</option>)}
          </select>
          <select aria-label="Stock status filter" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1) }} className="rounded-lg border bg-transparent px-3 py-2 text-sm">
            <option value="">All stock statuses</option>
            <option value="available">Available</option>
            <option value="out_of_stock">Out of stock</option>
            <option value="low_stock">Low stock</option>
            <option value="expired">Expired</option>
            <option value="expiring">Expiring within 30 days</option>
          </select>
        </div>

        {batchesQuery.isLoading && <div className="flex min-h-40 items-center justify-center"><Spinner className="h-8 w-8" /></div>}
        {batchesQuery.isError && (
          <p role="alert" className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">
            {requestError(batchesQuery.error, 'Inventory batches could not be loaded.')}
          </p>
        )}
        {batchesQuery.data && results.length === 0 && (
          <EmptyState title="No inventory batches found" description="No batches match the selected branch and filters." />
        )}
        {results.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-zinc-200 text-left text-sm dark:divide-zinc-800">
              <thead className="text-xs uppercase text-zinc-500">
                <tr>{['Medicine', 'Batch', 'Branch', 'Warehouse', 'Quantity', 'Selling price', 'Expiry', 'Status'].map((label) => <th key={label} className="px-3 py-3">{label}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {results.map((row) => (
                  <tr key={row.id}>
                    <td className="px-3 py-3 font-medium">{row.medicine_name}</td>
                    <td className="px-3 py-3">{row.batch_number}</td>
                    <td className="px-3 py-3">{row.branch_name}</td>
                    <td className="px-3 py-3">{row.warehouse_name ?? '—'}</td>
                    <td className="px-3 py-3">{formatNumber(row.quantity)}</td>
                    <td className="px-3 py-3">{formatCurrency(row.selling_price, 'AFN')}</td>
                    <td className="px-3 py-3">{row.expiry_date}</td>
                    <td className="px-3 py-3"><Badge tone={statusTone(row.status)}>{row.status.replaceAll('_', ' ')}</Badge></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="flex justify-between border-t px-3 py-3 text-sm">
              <span>Page {page} of {totalPages}</span>
              <div className="flex gap-2">
                <button type="button" disabled={page <= 1} onClick={() => setPage((current) => current - 1)} className="rounded border px-3 py-1 disabled:opacity-40">Previous</button>
                <button type="button" disabled={page >= totalPages} onClick={() => setPage((current) => current + 1)} className="rounded border px-3 py-1 disabled:opacity-40">Next</button>
              </div>
            </div>
          </div>
        )}
      </section>

      {canWrite && (
        <div className="grid gap-6 xl:grid-cols-2">
          <form onSubmit={submitMovement} className="space-y-3 rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="font-semibold">Record stock movement</h2>
            <select aria-label="Movement type" value={movementType} onChange={(event) => setMovementType(event.target.value as (typeof movementTypes)[number][0])} className="w-full rounded-lg border bg-transparent px-3 py-2 text-sm">
              {movementTypes.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
            <select aria-label="Batch for movement" required value={batchId} onChange={(event) => setBatchId(event.target.value)} className="w-full rounded-lg border bg-transparent px-3 py-2 text-sm">
              <option value="">Select a batch</option>
              {results.map((item) => <option key={item.id} value={item.id}>{item.medicine_name} · {item.batch_number} · {item.branch_name} ({item.quantity})</option>)}
            </select>
            <input aria-label="Movement quantity" inputMode="numeric" required value={quantity} onChange={(event) => setQuantity(event.target.value)} placeholder="Quantity" className="w-full rounded-lg border bg-transparent px-3 py-2 text-sm" />
            <input aria-label="Movement reference" value={reference} onChange={(event) => setReference(event.target.value)} placeholder="Reference (optional)" className="w-full rounded-lg border bg-transparent px-3 py-2 text-sm" />
            <textarea aria-label="Movement notes" value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Notes (optional)" className="w-full rounded-lg border bg-transparent px-3 py-2 text-sm" rows={2} />
            {movementFormError && <p role="alert" className="text-sm text-rose-600">{movementFormError}</p>}
            {movementMutation.isError && <p role="alert" className="text-sm text-rose-600">{requestError(movementMutation.error, 'Stock movement failed.')}</p>}
            {movementMutation.isSuccess && <p role="status" className="text-sm text-emerald-700">Stock movement recorded.</p>}
            <button disabled={movementMutation.isPending} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
              {movementMutation.isPending ? 'Recording…' : 'Record movement'}
            </button>
          </form>

          <form onSubmit={submitTransfer} className="space-y-3 rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
            <h2 className="font-semibold">Transfer stock between batches</h2>
            <select aria-label="Transfer source batch" required value={sourceBatch} onChange={(event) => setSourceBatch(event.target.value)} className="w-full rounded-lg border bg-transparent px-3 py-2 text-sm">
              <option value="">Source batch</option>
              {results.map((item) => <option key={item.id} value={item.id}>{item.medicine_name} · {item.batch_number} · {item.branch_name}</option>)}
            </select>
            <select aria-label="Transfer destination batch" required value={destinationBatch} onChange={(event) => setDestinationBatch(event.target.value)} className="w-full rounded-lg border bg-transparent px-3 py-2 text-sm">
              <option value="">Destination batch</option>
              {results.map((item) => <option key={item.id} value={item.id}>{item.medicine_name} · {item.batch_number} · {item.branch_name}</option>)}
            </select>
            <input aria-label="Transfer quantity" inputMode="numeric" required value={transferQuantity} onChange={(event) => setTransferQuantity(event.target.value)} placeholder="Quantity" className="w-full rounded-lg border bg-transparent px-3 py-2 text-sm" />
            {transferError && <p role="alert" className="text-sm text-rose-600">{transferError}</p>}
            <button disabled={transferMutation.isPending} className="rounded-lg bg-sky-700 px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
              {transferMutation.isPending ? 'Transferring…' : 'Transfer stock'}
            </button>
          </form>
        </div>
      )}

      <section className="space-y-3 rounded-xl border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-900">
        <h2 className="font-semibold">Recent inventory transactions</h2>
        {transactionsQuery.isLoading && <Spinner />}
        {transactionsQuery.isError && <p role="alert" className="text-sm text-rose-600">{requestError(transactionsQuery.error, 'Transaction history could not be loaded.')}</p>}
        {transactionsQuery.data?.results.length === 0 && <EmptyState title="No transactions recorded" description="Stock changes are recorded here as an immutable ledger." />}
        {transactionsQuery.data && transactionsQuery.data.results.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase text-zinc-500"><tr>{['Date', 'Type', 'Medicine / batch', 'Branch', 'Quantity', 'Reference'].map((label) => <th key={label} className="px-3 py-2">{label}</th>)}</tr></thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {transactionsQuery.data.results.map((item) => (
                  <tr key={item.id}>
                    <td className="px-3 py-2">{item.created_at}</td>
                    <td className="px-3 py-2">{item.transaction_type.replaceAll('_', ' ')}</td>
                    <td className="px-3 py-2">{item.medicine_name} · {item.batch_number}</td>
                    <td className="px-3 py-2">{item.branch_name}</td>
                    <td className="px-3 py-2">{item.direction === 'out' ? '−' : '+'}{item.quantity}</td>
                    <td className="px-3 py-2">{item.reference || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
