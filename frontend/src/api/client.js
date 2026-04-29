import axios from 'axios'

export function getAuthToken() {
  return localStorage.getItem('jwt_token') || sessionStorage.getItem('jwt_token')
}

const client = axios.create({
  baseURL: '/api',
})

client.interceptors.request.use(config => {
  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  response => response,
  error => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    const url = String(error.config?.url || '')
    const shouldResetSession = status === 401 && (
      url.includes('/auth/me') ||
      detail === 'Token expired' ||
      detail === 'Invalid token'
    )

    if (shouldResetSession) {
      localStorage.removeItem('jwt_token')
      sessionStorage.removeItem('jwt_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default client
