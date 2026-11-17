import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Leaf, ShieldCheck, Sun, Users, Wrench } from 'lucide-react'
import { demoUsers } from '../../mocks/mockData'

const roles = [
  { key: 'socio', label: 'Socio', icon: Users },
  { key: 'operatore', label: 'Operatore', icon: Wrench },
  { key: 'admin', label: 'Admin', icon: ShieldCheck }
]

export default function LoginPage() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({ email: 'maria.rossi@user.com', password: 'demo123' })

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    navigate('/socio/dashboard')
  }

  const handleQuickAccess = (roleKey) => {
    const user = demoUsers[roleKey]
    if (!user) return
    setFormData({ email: user.email, password: user.password })
    navigate(user.home)
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
            <button type="submit" className="h-11 w-full rounded-xl bg-gradient-primary font-semibold text-primary-foreground shadow-glow transition hover:brightness-105">Accedi</button>
          </form>

          <div className="my-6 flex items-center gap-3 text-xs text-muted-foreground">
            <span className="h-px flex-1 bg-border" /> Accesso demo <span className="h-px flex-1 bg-border" />
          </div>
          <div className="grid grid-cols-3 gap-2">
            {roles.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                type="button"
                onClick={() => handleQuickAccess(key)}
                className="flex flex-col items-center gap-1.5 rounded-xl border border-border bg-background py-3 text-xs font-semibold text-foreground transition hover:border-primary hover:bg-secondary"
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
