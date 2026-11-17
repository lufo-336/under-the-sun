export default function UrgencyBadge({ urgency }) {
  const normalized = (urgency || '').toLowerCase()
  const className = !normalized ? 'bg-muted text-muted-foreground' : normalized === 'alta' ? 'bg-destructive-soft text-destructive-foreground' : normalized === 'media' ? 'bg-accent-soft text-accent-strong' : 'bg-success-soft text-primary'
  const label = normalized ? normalized.charAt(0).toUpperCase() + normalized.slice(1) : 'Non classificata'

  return <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${className}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />{label}</span>
}
