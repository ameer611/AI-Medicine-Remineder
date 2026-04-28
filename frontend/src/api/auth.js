import client from './client'

export async function createSession() {
  const { data } = await client.post('/auth/session', {})
  return data
}

export async function checkSession(sessionId) {
  const { data } = await client.get(`/auth/session/${sessionId}`)
  return data
}

export async function getMe() {
  const { data } = await client.get('/auth/me')
  return data
}
