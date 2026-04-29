import { useEffect, useMemo, useState } from 'react'
import { format } from 'date-fns'
import { getActiveMedications } from '../api/medicines'
import { createIntakeLog, getUserIntakeLogs } from '../api/intakeLogs'
import { useAuth } from '../hooks/useAuth'
import MedicineCard from '../components/MedicineCard'
import IntakeButtons from '../components/IntakeButtons'
import LoadingSpinner from '../components/LoadingSpinner'

function getMedicationId(medication) {
  return medication.medication_id || medication.id || 0
}

function getSlotKey(medicationId, scheduleId, scheduledTime) {
  return `${medicationId}:${scheduleId ?? 'none'}:${scheduledTime}`
}

export default function Schedules() {
  const auth = useAuth()
  const [medications, setMedications] = useState([])
  const [logged, setLogged] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const today = useMemo(() => format(new Date(), 'yyyy-MM-dd'), [])

  useEffect(() => {
    if (!auth?.user?.telegram_id) return

    let active = true
    setLoading(true)
    setError('')

    Promise.all([
      getActiveMedications(auth.user.telegram_id),
      getUserIntakeLogs(auth.user.telegram_id, today, today),
    ])
      .then(([medicationData, logs]) => {
        if (!active) return
        setMedications(medicationData.medications || [])
        const nextLogged = {}
        logs.forEach(log => {
          nextLogged[getSlotKey(log.medication_id, log.schedule_id, log.scheduled_time)] = log.status
        })
        setLogged(nextLogged)
      })
      .catch(err => {
        if (!active) return
        const message = err?.response?.data?.detail || err?.message || 'Failed to load schedules'
        setError(message)
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [auth?.user?.telegram_id, today])

  const handleAction = async (medication, scheduleId, scheduledTime, status) => {
    if (status === 'felt_bad' && !window.confirm('Confirm that you feel bad after taking this dose?')) return

    const medicationId = getMedicationId(medication)
    const slotKey = getSlotKey(medicationId, scheduleId, scheduledTime)
    setError('')

    try {
      const log = await createIntakeLog({
        user_id: auth.user.id,
        medication_id: medicationId,
        schedule_id: scheduleId,
        scheduled_time: scheduledTime,
        scheduled_date: today,
        status,
      })
      setLogged(prev => ({ ...prev, [slotKey]: log.status }))
    } catch (err) {
      const message = err?.response?.data?.detail || err?.message || 'Failed to save intake log'
      setError(message)
    }
  }

  if (loading) return <LoadingSpinner label="Loading schedules..." />

  return (
    <section className="stack">
      <div className="hero">
        <span className="hero__eyebrow">Schedules</span>
        <h1>Your active schedules</h1>
        <p>Log each dose directly from the web app. Every button writes an intake log and updates the current row.</p>
      </div>
      {error ? <div className="empty">{error}</div> : null}

      {medications.length ? medications.map(med => (
        <MedicineCard key={med.name} medication={med}>
          <div className="stack">
            {med.times?.map((time, idx) => {
              const scheduleId = med.schedule_ids?.[idx] ?? null
              const slotKey = getSlotKey(getMedicationId(med), scheduleId, time)
              const recorded = logged[slotKey]
              return (
                <div className="panel" key={`${med.name}-${time}`}>
                  <div className="actions" style={{ justifyContent: 'space-between' }}>
                    <strong>{time}</strong>
                    {recorded ? <span className="status-pill">{recorded.replace('_', ' ')}</span> : null}
                  </div>
                  <IntakeButtons
                    disabled={Boolean(recorded)}
                    onAction={action => handleAction(med, scheduleId, time, action)}
                  />
                </div>
              )
            })}
          </div>
        </MedicineCard>
      )) : <div className="empty">You do not have any active schedules yet.</div>}
    </section>
  )
}
