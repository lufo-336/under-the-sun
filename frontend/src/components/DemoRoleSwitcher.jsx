import { useNavigate } from 'react-router-dom'

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
    <div className="demo-role-switcher">
      <span className="switcher-label">Modalità Wireframe — Cambia vista ruolo:</span>
      <div className="switcher-actions" aria-label="Selettore demo ruolo">
        {Object.entries(ROLE_LABELS).map(([role, label]) => (
          <button
            key={role}
            type="button"
            className={`role-pill ${currentRole === role ? 'active' : ''}`}
            onClick={() => handleRoleChange(role)}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  )
}
