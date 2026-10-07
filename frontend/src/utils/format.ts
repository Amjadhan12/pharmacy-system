/** Locale-aware formatting helpers (money uses exact decimal strings from the API). */

export function formatCurrency(
  amount: number | string | null | undefined,
  currency = 'USD',
  locale = 'en-US',
): string {
  if (amount === null || amount === undefined || amount === '') {
    return '—'
  }
  const value = typeof amount === 'string' ? Number(amount) : amount
  if (Number.isNaN(value)) return '—'
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatNumber(
  value: number | null | undefined,
  locale = 'en-US',
): string {
  if (value === null || value === undefined) return '—'
  return new Intl.NumberFormat(locale).format(value)
}

export function formatDate(
  value: string | Date | null | undefined,
  locale = 'en-US',
): string {
  if (!value) return '—'
  const date = typeof value === 'string' ? new Date(value) : value
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}
