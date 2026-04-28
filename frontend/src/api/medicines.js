import client from './client'

export async function uploadImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await client.post('/ocr', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function parsePrescription(text) {
  const { data } = await client.post('/parse', { text })
  return data
}

export async function saveMedication(payload) {
  const { data } = await client.post('/medications', payload)
  return data
}

export async function getActiveMedications(telegramId) {
  const { data } = await client.get(`/medications/${telegramId}/active`)
  return data
}
