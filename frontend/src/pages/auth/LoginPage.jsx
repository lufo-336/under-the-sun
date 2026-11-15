import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { demoUsers } from '../../mocks/mockData'

const roleMap = {
  socio: 'Socio',
  operatore: 'Operatore',
  admin: 'Admin'
}

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
    <div className="auth-page">
      <div className="auth-card">
        <p className="section-kicker">Accesso demo</p>
        <h2>Accedi a UnderTheSun</h2>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label>
            <span>Email</span>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="nome@esempio.it"
            />
          </label>

          <label>
            <span>Password</span>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="••••••••"
            />
          </label>

          <button type="submit" className="primary-button full-width">
            Accedi
          </button>
        </form>

        <div className="quick-access-panel">
          <p>Accesso rapido demo</p>
          <div className="quick-access-actions">
            {Object.entries(roleMap).map(([key, label]) => (
              <button key={key} type="button" className="secondary-button" onClick={() => handleQuickAccess(key)}>
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
