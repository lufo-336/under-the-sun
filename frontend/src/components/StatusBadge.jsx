export default function StatusBadge({ status }) {
  const normalized = (status || '').toLowerCase();
  return (
    <span className={`status-badge ${normalized === 'in_corso' ? 'in-progress' : normalized === 'chiusa' ? 'closed' : 'open'}`}> 
      {normalized === 'in_corso' ? 'In corso' : normalized === 'chiusa' ? 'Chiusa' : 'Aperta'}
    </span>
  )
}
