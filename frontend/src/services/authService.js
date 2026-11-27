import apiClient from './apiClient'

const TOKEN_KEY = 'under_the_sun_token'
const USER_KEY = 'under_the_sun_user'

export const authService = {
  getToken: () => localStorage.getItem(TOKEN_KEY),
  getStoredUser: () => {
    const value = localStorage.getItem(USER_KEY)
    if (!value) return null

    try {
      return JSON.parse(value)
    } catch {
      localStorage.removeItem(USER_KEY)
      return null
    }
  },
  login: async (email, password) => {
    const data = await apiClient.post('/auth/login', { email, password })

    if (!data?.token || !data?.utente) {
      throw new Error('Risposta di login non valida')
    }

    localStorage.setItem(TOKEN_KEY, data.token)
    localStorage.setItem(USER_KEY, JSON.stringify(data.utente))
    return data
  },
  me: async () => {
    const token = localStorage.getItem(TOKEN_KEY)
    const data = await apiClient.get('/auth/me', { token })
    const user = data?.utente ?? data

    if (!user?.ruolo) {
      throw new Error('Utente non valido')
    }

    localStorage.setItem(USER_KEY, JSON.stringify(user))
    return user
  },
  logout: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }
}

export default authService
