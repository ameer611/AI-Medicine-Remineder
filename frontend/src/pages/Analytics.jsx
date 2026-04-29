import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { getUserAnalytics, getSupervisorAnalytics } from '../api/analytics'
import LoadingSpinner from '../components/LoadingSpinner'
import { AdherenceBarChart, AdherenceLineChart } from '../components/AdherenceChart'

function toTimeline(logs) {
  const grouped = new Map()
  logs.forEach(log => {
    const key = log.scheduled_date
    const entry = grouped.get(key) || { date: key, total: 0, consumed: 0 }
    entry.total += 1
    if (log.status === 'consumed') entry.consumed += 1
    grouped.set(key, entry)
  })
  return [...grouped.values()]
    .sort((a, b) => String(a.date).localeCompare(String(b.date)))
    .map(item => ({ date: item.date, rate: item.total ? Math.round((item.consumed / item.total) * 100) : 0 }))
}

export default function Analytics() {
  const auth = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let active = true

    if (auth?.loading) {
      return () => {
        active = false
      }
    }

    if (!auth?.user?.telegram_id) {
      if (active) {
        setLoading(false)
        setData(null)
        setError(null)
      }
      return () => {
        active = false
      }
    }

    setLoading(true)
    setError(null)
    const loader = auth.user.role === 'supervisor'
      ? getSupervisorAnalytics(auth.user.telegram_id)
      : getUserAnalytics(auth.user.telegram_id)

    loader
      .then(result => {
        if (active) setData(result)
      })
      .catch(err => {
        if (active) {
          const message = err?.response?.data?.detail || err?.response?.data?.message || err?.message || 'Failed to load analytics'
          setError(message)
          setData(null)
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [auth?.loading, auth?.user?.telegram_id, auth?.user?.role])

  const lineData = useMemo(() => toTimeline(data?.logs || []), [data])
  const barData = useMemo(() => {
    if (!data?.stats) return []
    return [
      { name: 'Consumed', value: data.stats.consumed || 0 },
      { name: 'Skipped', value: data.stats.not_consumed || 0 },
      { name: 'Feeling bad', value: data.stats.felt_bad || 0 },
    ]
  }, [data])
  const hasIntakeData = (data?.stats?.total_scheduled || 0) > 0 || (data?.logs || []).length > 0

  if (auth?.loading || loading) return <LoadingSpinner label="Loading analytics..." />

  if (!auth?.user) {
    return (
      <section className="stack">
        <div className="hero">
          <span className="hero__eyebrow">Analytics</span>
          <h1>Authentication required</h1>
          <p>Sign in to view your medication adherence analytics.</p>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="stack">
        <div className="hero">
          <span className="hero__eyebrow">Analytics</span>
          <h1>Unable to load analytics</h1>
          <p className="muted">{error}</p>
        </div>
      </section>
    )
  }

  if (!data) {
    return (
      <section className="stack">
        <div className="hero">
          <span className="hero__eyebrow">Analytics</span>
          <h1>{auth.user.role === 'supervisor' ? 'Supervisor dashboard' : 'Your adherence dashboard'}</h1>
          <p>No intake data yet. Start logging medicines to see your analytics.</p>
        </div>
      </section>
    )
  }

  return (
    <section className="stack">
      <div className="hero">
        <span className="hero__eyebrow">Analytics</span>
        <h1>{auth?.user?.role === 'supervisor' ? 'Supervisor dashboard' : 'Your adherence dashboard'}</h1>
        <p>Review adherence, compare medication trends, and keep an eye on intake history.</p>
      </div>

      {data?.stats ? (
        <div className="grid grid--3">
          <div className="card"><h3>Total scheduled</h3><p className="muted">{data.stats.total_scheduled}</p></div>
          <div className="card"><h3>Consumed</h3><p className="muted">{data.stats.consumed}</p></div>
          <div className="card"><h3>Adherence rate</h3><p className="muted">{Math.round(data.stats.adherence_rate)}%</p></div>
        </div>
      ) : null}

      {hasIntakeData ? (
        <div className="grid grid--2">
          <AdherenceLineChart data={lineData} />
          <AdherenceBarChart data={barData} title="Intake status breakdown" />
        </div>
      ) : (
        <div className="empty">No intake logs found yet.</div>
      )}

      {Array.isArray(data?.by_medication) && data.by_medication.length ? (
        <div className="card stack">
          <h3>Per-medication breakdown</h3>
          <div className="grid grid--2">
            {data.by_medication.map(item => (
              <div className="panel" key={item.medication_id}>
                <strong>{item.medication_name}</strong>
                <div className="muted">{item.stats.total_scheduled} scheduled · {Math.round(item.stats.adherence_rate)}% adherence</div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {auth?.user?.role === 'supervisor' ? (
        <div className="card stack">
          <h3>Connected users</h3>
          {(data?.users || []).length ? data.users.map(row => (
            <div className="panel" key={row.user.id}>
              <strong>{row.user.full_name || 'User'}</strong>
              <div className="muted">{row.user.phone_number || '—'} · {row.stats.total_scheduled} scheduled · {Math.round(row.stats.adherence_rate)}%</div>
            </div>
          )) : <div className="empty">No supervised users found.</div>}
        </div>
      ) : null}
    </section>
  )
}
