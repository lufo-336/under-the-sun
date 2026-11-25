import { useEffect, useMemo, useState } from 'react'
import { AuthContext } from './authContext'
import authService from '../services/authService'

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => authService.getToken())
  const [user, setUser] = useState(() => authService.getStoredUser())
  const [loading, setLoading] = useState(() => Boolean(authService.getToken()))

  useEffect(() => {
    if (!token) return

    let active = true

    authService.me()
      .then((currentUser) => {
        if (active) setUser(currentUser)
      })
      .catch(() => {
        if (active) {
          authService.logout()
          setToken(null)
          setUser(null)
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [token])

  useEffect(() => {
    const handleUnauthorized = () => {
      authService.logout()
      setToken(null)
      setUser(null)
      setLoading(false)
    }

    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [])

  const login = async (email, password) => {
    const data = await authService.login(email, password)
    setToken(data.token)
    setUser(data.utente)
    setLoading(false)
    return data.utente
  }

  const logout = () => {
    authService.logout()
    setToken(null)
    setUser(null)
  }

  const value = useMemo(() => ({
    token,
    user,
    loading,
    isAuthenticated: Boolean(token && user),
    login,
    logout
  }), [token, user, loading])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
