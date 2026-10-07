import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import Badge from '@/components/ui/Badge'
import EmptyState from '@/components/ui/EmptyState'
import Spinner from '@/components/ui/Spinner'
import { apiGet, ApiRequestError } from '@/services/api'
import type { Paginated } from '@/types/api'
import { formatCurrency, formatNumber } from '@/utils/format'

interface MedicineRecord {
  id: number
  generic_name: string
  brand_name: string
  manufacturer_name: string | null
  category_name: string
  dosage_form_name: string
  strength: string
  route: string
  barcode: string | null
  gtin: string | null
  prescription_required: boolean
  reorder_level: number
  storage_condition: string
  is_active: boolean
}

interface BatchRecord {
  id: number
  batch_number: string
  purchase_price: string
  selling_price: string
  quantity: number
  manufacture_date: string | null
  expiry_date: string
  status: string
  branch_name: string
  warehouse_name: string | null
}

export default function MedicineDetailPage() {
  const { medicineId } = useParams()
  const detailQuery = useQuery({
    queryKey: ['medicine-detail', medicineId],
    enabled: Boolean(medicineId),
    queryFn: async () => {
      const response = await apiGet<MedicineRecord>(
        `/medicines/medicines/${medicineId}/`,
      )
      return response
    },
  })
  const batchesQuery = useQuery({
    queryKey: ['medicine-batches', medicineId],
    enabled: Boolean(medicineId),
    queryFn: () =>
      apiGet<Paginated<BatchRecord>>('/inventory/', {
        params: { medicine: medicineId, page: 1 },
      }),
  })

  if (detailQuery.isLoading) {
    return <div className="flex min-h-40 items-center justify-center"><Spinner className="h-8 w-8" /></div>
  }
  if (detailQuery.isError || !detailQuery.data) {
    return (
      <div role="alert" className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">
        {detailQuery.error instanceof ApiRequestError
          ? detailQuery.error.message
          : 'Medicine details could not be loaded.'}
      </div>
    )
  }
  const medicine = detailQuery.data

  return (
    <div className="space-y-6">
      <Link to="/medicines" className="text-sm text-emerald-700 hover:underline dark:text-emerald-400">
        ← Back to medicines
      </Link>
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{medicine.generic_name}</h1>
          <p className="mt-1 text-zinc-500">
            {[medicine.brand_name, medicine.strength].filter(Boolean).join(' · ') || 'No brand or strength recorded'}
          </p>
        </div>
        <Badge tone={medicine.is_active ? 'success' : 'neutral'}>
          {medicine.is_active ? 'Active' : 'Inactive'}
        </Badge>
      </header>

      <dl className="grid gap-4 rounded-xl border border-zinc-200 bg-white p-5 text-sm dark:border-zinc-800 dark:bg-zinc-900 sm:grid-cols-2 lg:grid-cols-3">
        {[
          ['Category', medicine.category_name],
          ['Dosage form', medicine.dosage_form_name],
          ['Manufacturer', medicine.manufacturer_name ?? '—'],
          ['Route', medicine.route],
          ['Barcode', medicine.barcode ?? '—'],
          ['GTIN', medicine.gtin ?? '—'],
          ['Prescription required', medicine.prescription_required ? 'Yes' : 'No'],
          ['Low-stock threshold', formatNumber(medicine.reorder_level)],
          ['Storage', medicine.storage_condition.replaceAll('_', ' ')],
        ].map(([label, value]) => (
          <div key={label}>
            <dt className="text-zinc-500">{label}</dt>
            <dd className="mt-1 font-medium">{value}</dd>
          </div>
        ))}
      </dl>

      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-semibold">Medicine batches</h2>
          <p className="text-sm text-zinc-500">Branch-scoped batches ordered by earliest expiry.</p>
        </div>
        {batchesQuery.isLoading && <Spinner />}
        {batchesQuery.isError && (
          <p role="alert" className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700">
            {batchesQuery.error instanceof ApiRequestError
              ? batchesQuery.error.message
              : 'Batch records could not be loaded.'}
          </p>
        )}
        {batchesQuery.data?.results.length === 0 && (
          <EmptyState title="No batches recorded" description="There are no accessible batches for this medicine." />
        )}
        {batchesQuery.data && batchesQuery.data.results.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
            <table className="min-w-full text-left text-sm">
              <thead className="text-xs uppercase text-zinc-500">
                <tr>{['Batch', 'Purchase price', 'Selling price', 'Quantity', 'Manufactured', 'Expiry', 'Branch', 'Warehouse', 'Status'].map((label) => <th key={label} className="px-3 py-3">{label}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-zinc-100 dark:divide-zinc-800">
                {batchesQuery.data.results.map((batch) => (
                  <tr key={batch.id}>
                    <td className="px-3 py-3">{batch.batch_number}</td>
                    <td className="px-3 py-3">{formatCurrency(batch.purchase_price, 'AFN')}</td>
                    <td className="px-3 py-3">{formatCurrency(batch.selling_price, 'AFN')}</td>
                    <td className="px-3 py-3">{formatNumber(batch.quantity)}</td>
                    <td className="px-3 py-3">{batch.manufacture_date ?? '—'}</td>
                    <td className="px-3 py-3">{batch.expiry_date}</td>
                    <td className="px-3 py-3">{batch.branch_name}</td>
                    <td className="px-3 py-3">{batch.warehouse_name ?? '—'}</td>
                    <td className="px-3 py-3"><Badge tone={batch.status === 'expired' || batch.status === 'damaged' ? 'danger' : batch.status === 'available' ? 'success' : 'warning'}>{batch.status.replaceAll('_', ' ')}</Badge></td>
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
