import { useNavigate } from 'react-router-dom'
import { Sun } from 'lucide-react'

const ROLE_HOME = {
  socio: '/socio/dashboard',
  operatore: '/operatore/impianti',
  admin: '/admin/kpi',
  login: '/login'
}

const ROLE_LABELS = {
  socio: 'Socio',
  operatore: 'Operatore',
  admin: 'Admin',
  login: 'Login'
}

export default function DemoRoleSwitcher({ currentRole = 'socio' }) {
  const navigate = useNavigate()

  const handleRoleChange = (role) => {
    const target = ROLE_HOME[role] || '/socio/dashboard'
    navigate(target)
  }

  return (
    <div className="sticky top-0 z-40 bg-ink text-ink-foreground">
      <div className="mx-auto flex max-w-7xl items-center gap-3 overflow-x-auto px-4 py-2">
        <span className="hidden shrink-0 items-center gap-1.5 text-xs font-extrabold tracking-tight sm:flex"><Sun className="h-4 w-4 text-accent" /> UnderTheSun</span>
        <span className="hidden shrink-0 text-[11px] font-semibold uppercase tracking-wider opacity-60 sm:inline">Demo · ruolo</span>
        <div className="flex shrink-0 gap-1 rounded-full bg-ink-foreground/10 p-1" aria-label="Selettore demo ruolo">
          {Object.entries(ROLE_LABELS).map(([role, label]) => (
            <button
              key={role}
              type="button"
              className={`rounded-full px-3 py-1 text-xs font-semibold transition ${currentRole === role ? 'bg-primary text-primary-foreground' : 'opacity-75 hover:opacity-100'}`}
              onClick={() => handleRoleChange(role)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
