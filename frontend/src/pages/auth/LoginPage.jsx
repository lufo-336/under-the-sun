import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Leaf, ShieldCheck, Sun, Users, Wrench } from 'lucide-react'
import { useAuth } from '../../context/useAuth'

const roles = [
  { key: 'socio', label: 'Socio', icon: Users },
  { key: 'operatore', label: 'Operatore', icon: Wrench },
  { key: 'admin', label: 'Admin', icon: ShieldCheck }
]

const roleHomes = {
  socio: '/socio/dashboard',
  operatore: '/operatore/impianti',
  admin: '/admin/kpi'
}

const demoCredentials = {
  socio: { email: 'socio1@example.com', password: 'prova1234' },
  operatore: { email: 'operatore@example.com', password: 'prova1234' },
  admin: { email: 'admin@example.com', password: 'prova1234' }
}

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login, isAuthenticated, user } = useAuth()
  const [formData, setFormData] = useState({ email: 'socio1@example.com', password: 'prova1234' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated && user) {
      navigate(roleHomes[user.ruolo] || '/login', { replace: true })
    }
  }, [isAuthenticated, navigate, user])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleLogin = async (credentials = formData) => {
    setError('')
    setLoading(true)

    try {
      const authenticatedUser = await login(credentials.email, credentials.password)
      const returnTo = location.state?.from
      const rolePrefix = authenticatedUser.ruolo === 'socio' ? '/socio/'
        : authenticatedUser.ruolo === 'operatore' ? '/operatore/'
          : authenticatedUser.ruolo === 'admin' ? '/admin/' : null
      const destination = returnTo?.startsWith(rolePrefix) ? returnTo : roleHomes[authenticatedUser.ruolo]
      navigate(destination || '/login', { replace: true })
    } catch (requestError) {
      setError(requestError.message
        || (requestError.status === 401 ? 'Email o password non corrette.' : 'Impossibile accedere al backend.'))
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    handleLogin()
  }

  const handleQuickAccess = (roleKey) => {
    const credentials = demoCredentials[roleKey]
    if (!credentials) return
    setFormData(credentials)
    handleLogin(credentials)
  }

  return (
    <div className="grid min-h-[calc(100vh-44px)] place-items-center bg-page px-4 py-10">
      <div className="w-full max-w-md">
        <div className="rounded-3xl border border-border bg-card p-7 shadow-soft sm:p-9">
          <div className="flex min-w-0 items-center gap-2.5">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-gradient-sun text-primary-foreground shadow-glow">
              <Sun className="h-7 w-7" aria-hidden="true" />
            </span>
            <span className="min-w-0 leading-tight">
              <span className="block truncate text-2xl font-extrabold tracking-tight text-foreground">UnderTheSun</span>
              <span className="block truncate text-[11px] font-semibold uppercase tracking-wider text-primary">CER Buby Green</span>
            </span>
          </div>

          <h1 className="mt-8 text-2xl font-extrabold tracking-tight text-foreground">Bentornato nella tua comunità</h1>
          <p className="mt-1 text-sm text-muted-foreground">Energia pulita, condivisa sotto lo stesso sole.</p>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="grid gap-1.5 text-sm font-medium text-foreground">
              Email
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="nome@esempio.it"
                className="h-11 rounded-xl border border-input bg-background px-3"
              />
            </label>
            <label className="grid gap-1.5 text-sm font-medium text-foreground">
              Password
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                className="h-11 rounded-xl border border-input bg-background px-3"
              />
            </label>
            {error && <p role="alert" className="rounded-xl bg-destructive-soft px-3 py-2 text-sm font-semibold text-destructive-foreground">{error}</p>}
            <button type="submit" disabled={loading} className="h-11 w-full rounded-xl bg-gradient-primary font-semibold text-primary-foreground shadow-glow transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-60">
              {loading ? 'Accesso…' : 'Accedi'}
            </button>
          </form>

          <div className="my-6 flex items-center gap-3 text-xs text-muted-foreground">
            <span className="h-px flex-1 bg-border" /> Accesso demo <span className="h-px flex-1 bg-border" />
          </div>
          <div className="grid grid-cols-3 gap-2">
            {roles.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                type="button"
                disabled={loading}
                onClick={() => handleQuickAccess(key)}
                className="flex flex-col items-center gap-1.5 rounded-xl border border-border bg-background py-3 text-xs font-semibold text-foreground transition hover:border-primary hover:bg-secondary disabled:opacity-60"
              >
                <Icon className="h-5 w-5 text-primary" aria-hidden="true" /> {label}
              </button>
            ))}
          </div>
        </div>
        <p className="mt-5 flex items-center justify-center gap-1.5 text-xs text-muted-foreground">
          <Leaf className="h-3.5 w-3.5 text-primary" aria-hidden="true" /> Comunità Energetica Rinnovabile Buby Green
        </p>
      </div>
    </div>
  )
}
