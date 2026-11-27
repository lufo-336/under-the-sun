import { Activity } from 'lucide-react'
import { formatCurrency, formatKg, formatNumber } from '../utils/formatters'

export default function KpiCard({ label, value, suffix, helper, tone = 'emerald', icon: Icon = Activity, format }) {
  const formatInteger = (number) => {
    const numericValue = Number(number ?? 0)

    if (Math.abs(numericValue) >= 1000 && Math.abs(numericValue) < 10000) {
      return new Intl.NumberFormat('it-IT', { useGrouping: 'always', maximumFractionDigits: 0 }).format(numericValue)
    }

    return formatNumber(numericValue, 0)
  }

  const formatValue = () => {
    const normalizedLabel = String(label ?? '').toLowerCase()

    if (value == null) {
      return '—'
    }

    if (typeof value === 'number' && (format === 'eur' || normalizedLabel.includes('€') || normalizedLabel.includes('euro'))) {
      return formatCurrency(value)
    }

    if (typeof value === 'number' && normalizedLabel.includes('co2')) {
      return formatKg(value)
    }

    if (typeof value === 'number') {
      return `${formatInteger(value)}${suffix ? ` ${suffix}` : ''}`
    }

    return value
  }

  return (
    <article className="relative overflow-hidden rounded-2xl border border-border bg-card p-5 shadow-soft">
      <span className={`absolute inset-x-0 top-0 h-1 ${tone === 'amber' || tone === 'sun' ? 'bg-gradient-sun' : tone === 'slate' ? 'bg-muted-foreground' : 'bg-gradient-primary'}`} />
      <div className="flex items-center gap-3">
        <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${tone === 'amber' || tone === 'sun' ? 'bg-accent-soft text-accent-strong' : tone === 'slate' ? 'bg-muted text-muted-foreground' : 'bg-success-soft text-primary'}`}>
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
        <p className="min-w-0 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{label}</p>
      </div>
      <p className="mt-4 text-3xl font-extrabold tracking-tight text-foreground tabular-nums">{formatValue()}</p>
      {helper && <p className="mt-1 text-xs text-muted-foreground">{helper}</p>}
    </article>
  )
}
