import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/useAuth'

const roleHomes = {
  socio: '/socio/dashboard',
  operatore: '/operatore/impianti',
  admin: '/admin/kpi'
}

export default function ProtectedRoute({ allowedRole, children }) {
  const { isAuthenticated, loading, user } = useAuth()
  const location = useLocation()

  if (loading) {
    return <div className="grid min-h-screen place-items-center bg-page text-sm text-muted-foreground">Caricamento…</div>
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (allowedRole && user.ruolo !== allowedRole) {
    return <Navigate to={roleHomes[user.ruolo] || '/login'} replace />
  }

  return children
}
