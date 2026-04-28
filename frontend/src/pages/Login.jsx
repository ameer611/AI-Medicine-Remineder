import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createSession, checkSession } from '../api/auth'
import { useAuth } from '../hooks/useAuth'
import { usePolling } from '../hooks/usePolling'
import LoadingSpinner from '../components/LoadingSpinner'

export default function Login() {
  const auth = useAuth()
  const navigate = useNavigate()
  const [session, setSession] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let alive = true
    createSession()
      .then(data => alive && setSession(data))
      .catch(() => alive && setError('Could not create a login session.'))
    return () => {
      alive = false
    }
  }, [])

  const task = useMemo(() => {
    if (!session?.session_id) return null
    return () => checkSession(session.session_id)
  }, [session?.session_id])

  const { result, running } = usePolling(task || (async () => ({ authenticated: false })), 2000, Boolean(session?.session_id))

  useEffect(() => {
    if (result?.authenticated && result.jwt_token) {
      auth.loginWithToken(result.jwt_token).then(() => navigate('/'))
    }
  }, [result, auth, navigate])

  const restart = async () => {
    setError('')
    setSession(null)
    const data = await createSession()
    setSession(data)
  }

  if (!session && !error) return <LoadingSpinner label="Starting Telegram login..." />

  return (
    <section className="hero">
      <span className="hero__eyebrow">Telegram web login</span>
      <h1>Login with Telegram</h1>
      <p>Open Telegram, confirm the deep-link, and return here. We’ll poll the session until the bot attaches your account.</p>
      {error ? <div className="empty">{error}</div> : null}
      {session ? (
        <div className="stack">
          <a className="btn btn--primary" href={session.bot_start_link} target="_blank" rel="noreferrer">
            Login with Telegram
          </a>
          <div className="panel">
            <div className="actions" style={{ justifyContent: 'space-between' }}>
              <span className="muted">{running ? 'Waiting for Telegram confirmation...' : 'Polling stopped.'}</span>
              <span className="status-pill">Session active</span>
            </div>
          </div>
        </div>
      ) : null}
      {!running && !error ? (
        <button className="btn" type="button" onClick={restart}>Try again</button>
      ) : null}
    </section>
  )
}
