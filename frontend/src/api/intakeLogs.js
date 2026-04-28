import client from './client'

export async function createIntakeLog(payload) {
  const { data } = await client.post('/intake-logs', payload)
  return data
}

export async function getUserIntakeLogs(telegramId, startDate, endDate) {
  const params = new URLSearchParams()
  if (startDate) params.set('start_date', startDate)
  if (endDate) params.set('end_date', endDate)
  const { data } = await client.get(`/intake-logs/user/${telegramId}?${params.toString()}`)
  return data
}
