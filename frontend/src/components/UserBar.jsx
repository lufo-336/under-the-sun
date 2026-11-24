import { LogOut, Sun } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/useAuth'

const ROLE_LABELS = {
  socio: 'Socio',
  operatore: 'Operatore',
  admin: 'Admin'
}

export default function UserBar({ role }) {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const currentRole = user?.ruolo || role
  const roleLabel = ROLE_LABELS[currentRole] || currentRole

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="sticky top-0 z-40 bg-ink text-ink-foreground">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-2">
        <span className="hidden shrink-0 items-center gap-1.5 text-xs font-extrabold tracking-tight sm:flex">
          <Sun className="h-4 w-4 text-accent" aria-hidden="true" /> UnderTheSun
        </span>
        <span className="hidden shrink-0 text-[11px] font-semibold uppercase tracking-wider opacity-60 sm:inline">
          Area {roleLabel}
        </span>
        <div className="ml-auto flex min-w-0 items-center gap-2.5">
          <span className="min-w-0 truncate text-xs font-semibold opacity-90">{user?.email || 'Utente'}</span>
          <span className="shrink-0 rounded-full bg-ink-foreground/10 px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider">
            {roleLabel}
          </span>
          <button
            type="button"
            onClick={handleLogout}
            className="flex shrink-0 items-center gap-1.5 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground transition hover:brightness-105"
          >
            <LogOut className="h-3.5 w-3.5" aria-hidden="true" /> Esci
          </button>
        </div>
      </div>
    </div>
  )
}
