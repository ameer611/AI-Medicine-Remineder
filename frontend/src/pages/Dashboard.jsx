import { useAuth } from '../hooks/useAuth'

export default function Dashboard() {
  const auth = useAuth()

  return (
    <section className="stack">
      <div className="hero">
        <span className="hero__eyebrow">Overview</span>
        <h1>Welcome back{auth?.user?.full_name ? `, ${auth.user.full_name}` : ''}.</h1>
        <p>
          Track prescriptions, review schedules, and log intake actions without leaving the browser.
        </p>
      </div>

      <div className="grid grid--3">
        <div className="card"><h3>Role</h3><p className="muted">{auth?.user?.role || 'user'}</p></div>
        <div className="card"><h3>Phone</h3><p className="muted">{auth?.user?.phone_number || '—'}</p></div>
        <div className="card"><h3>Supervisor</h3><p className="muted">{auth?.user?.supervisor_id ?? '—'}</p></div>
      </div>
    </section>
  )
}
