export default function StatusBadge({ status }) {
  const normalized = (status || '').toLowerCase()
  return (
    <span className={`status-badge ${normalized === 'chiusa' ? 'closed' : 'open'}`}>
      {normalized === 'chiusa' ? 'Chiusa' : 'Aperta'}
    </span>
  )
}
