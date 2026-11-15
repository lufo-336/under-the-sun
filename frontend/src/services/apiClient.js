const API_BASE_URL = '/api'

async function request(endpoint, { method = 'GET', body, token, headers = {} } = {}) {
  const config = {
    method,
    headers: {
      ...headers
    }
  }

  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  if (body && !(body instanceof FormData)) {
    config.headers['Content-Type'] = 'application/json'
    config.body = JSON.stringify(body)
  } else if (body instanceof FormData) {
    config.body = body
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config)

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(errorText || 'Errore di richiesta API')
  }

  const contentType = response.headers.get('content-type') || ''
  return contentType.includes('application/json') ? response.json() : response.text()
}

export const apiClient = {
  get: (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'POST', body }),
  put: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'PUT', body }),
  patch: (endpoint, body, options = {}) => request(endpoint, { ...options, method: 'PATCH', body })
}

export default apiClient
