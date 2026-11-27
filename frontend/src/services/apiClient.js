const API_BASE_URL = '/api'

export class ApiError extends Error {
  constructor(codice, messaggio, status) {
    super(messaggio)
    this.name = 'ApiError'
    this.codice = codice
    this.status = status
  }
}

async function request(endpoint, { method = 'GET', body, token, headers = {} } = {}) {
  const config = {
    method,
    headers: {
      ...headers
    }
  }

  const accessToken = token || localStorage.getItem('under_the_sun_token')
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  if (body && !(body instanceof FormData)) {
    config.headers['Content-Type'] = 'application/json'
    config.body = JSON.stringify(body)
  } else if (body instanceof FormData) {
    config.body = body
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config)
  const contentType = response.headers.get('content-type') || ''
  let data = null

  if (contentType.includes('application/json')) {
    data = await response.json().catch(() => null)
  } else {
    data = await response.text()
  }

  if (!response.ok) {
    const errore = data?.errore
    if (response.status === 401) {
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
    }
    throw new ApiError(
      errore?.codice || (response.status === 401 ? 'CREDENZIALI_ERRATE' : 'ERRORE_API'),
      errore?.messaggio || (typeof data === 'string' && data) || 'Errore di richiesta API',
      response.status
    )
  }

  return data
}

export const apiClient = {
  get: (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'POST', body }),
  put: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'PUT', body }),
  patch: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'PATCH', body })
}

export default apiClient
