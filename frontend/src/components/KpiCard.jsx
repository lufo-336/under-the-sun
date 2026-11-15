import { formatCurrency, formatKg, formatNumber } from '../utils/formatters'

export default function KpiCard({ label, value, suffix, helper, tone = 'emerald' }) {
  const formatValue = () => {
    if (typeof value === 'number' && label.toLowerCase().includes('euro')) {
      return formatCurrency(value)
    }

    if (typeof value === 'number' && label.toLowerCase().includes('co2')) {
      return formatKg(value)
    }

    if (typeof value === 'number') {
      return `${formatNumber(value, 0)}${suffix ? ` ${suffix}` : ''}`
    }

    return value
  }

  return (
    <article className={`kpi-card tone-${tone}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{formatValue()}</div>
      {helper && <div className="kpi-helper">{helper}</div>}
    </article>
  )
}
