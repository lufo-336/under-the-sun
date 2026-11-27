export const formatNumber = (value, decimals = 0) =>
  new Intl.NumberFormat('it-IT', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  }).format(Number(value ?? 0))

export const formatCurrency = (value) =>
  new Intl.NumberFormat('it-IT', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(Number(value ?? 0))

export const formatKg = (value) => `${formatNumber(value, 0)} kg`

export const formatUtcToItalianDate = (isoString, options = {}) => {
  if (!isoString) return '—'

  const date = new Date(isoString)
  if (Number.isNaN(date.getTime())) return '—'

  return new Intl.DateTimeFormat('it-IT', {
    timeZone: 'Europe/Rome',
    ...options
  }).format(date)
}

export const formatDateTime = (isoString) =>
  formatUtcToItalianDate(isoString, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })

export const formatShortDate = (isoString) =>
  formatUtcToItalianDate(isoString, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
