export default function StatusBadge({ status }) {
  const normalized = (status || '').toLowerCase()
  const label = normalized === 'chiusa' ? 'Chiusa' : normalized === 'in_corso' ? 'In corso' : normalized === 'aperta' ? 'Aperta' : 'Non classificato'
  const tone = normalized === 'chiusa' ? 'bg-success-soft text-primary' : normalized === 'in_corso' ? 'bg-accent-soft text-accent-strong' : normalized === 'aperta' ? 'bg-destructive-soft text-destructive-foreground' : 'bg-muted text-muted-foreground'

  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${tone}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  )
}
