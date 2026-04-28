import { useEffect, useMemo, useState } from 'react'
import { format } from 'date-fns'
import { getActiveMedications } from '../api/medicines'
import { createIntakeLog } from '../api/intakeLogs'
import { useAuth } from '../hooks/useAuth'
import MedicineCard from '../components/MedicineCard'
import IntakeButtons from '../components/IntakeButtons'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Schedules() {
  const auth = useAuth()
  const [medications, setMedications] = useState([])
  const [logged, setLogged] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!auth?.user?.telegram_id) return
    setLoading(true)
    getActiveMedications(auth.user.telegram_id)
      .then(data => setMedications(data.medications || []))
      .finally(() => setLoading(false))
  }, [auth?.user?.telegram_id])

  const today = useMemo(() => format(new Date(), 'yyyy-MM-dd'), [])

  const handleAction = async (medication, scheduleId, scheduledTime, status) => {
    if (status === 'felt_bad' && !window.confirm('Confirm that you feel bad after taking this dose?')) return

    await createIntakeLog({
      user_id: auth.user.id,
      medication_id: medication.medication_id || medication.id || 0,
      schedule_id: scheduleId,
      scheduled_time: scheduledTime,
      scheduled_date: today,
      status,
    })
    setLogged(prev => ({ ...prev, [scheduleId]: status }))
  }

  if (loading) return <LoadingSpinner label="Loading schedules..." />

  return (
    <section className="stack">
      <div className="hero">
        <span className="hero__eyebrow">Schedules</span>
        <h1>Your active schedules</h1>
        <p>Log each dose directly from the web app. Every button writes an intake log and updates the current row.</p>
      </div>

      {medications.length ? medications.map(med => (
        <MedicineCard key={med.name} medication={med}>
          <div className="stack">
            {med.times?.map((time, idx) => {
              const scheduleId = med.schedule_ids?.[idx] ?? idx
              const recorded = logged[scheduleId]
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
