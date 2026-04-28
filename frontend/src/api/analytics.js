import client from './client'

export async function getUserAnalytics(telegramId, startDate, endDate) {
  const params = new URLSearchParams()
  if (startDate) params.set('start_date', startDate)
  if (endDate) params.set('end_date', endDate)
  const { data } = await client.get(`/analytics/user/${telegramId}?${params.toString()}`)
  return data
}

export async function getSupervisorAnalytics(telegramId, startDate, endDate) {
  const params = new URLSearchParams()
  if (startDate) params.set('start_date', startDate)
  if (endDate) params.set('end_date', endDate)
  const { data } = await client.get(`/analytics/supervisor/${telegramId}?${params.toString()}`)
  return data
}
