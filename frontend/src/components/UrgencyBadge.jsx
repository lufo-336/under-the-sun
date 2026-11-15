export default function UrgencyBadge({ urgency }) {
  const normalized = (urgency || '').toLowerCase()
  const className = normalized === 'alta' ? 'high' : normalized === 'media' ? 'medium' : 'low'

  return <span className={`urgency-badge ${className}`}>{normalized ? normalized.charAt(0).toUpperCase() + normalized.slice(1) : 'Bassa'}</span>
}
