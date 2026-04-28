import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function NavBar() {
  const auth = useAuth()

  return (
    <header className="nav">
      <Link to="/" className="nav__brand">
        <span className="nav__title">Dori Scheduler</span>
        <span className="nav__subtitle">Medication reminders and adherence</span>
      </Link>

      <nav className="nav__links">
        <NavLink className="nav__link" to="/medicines">Medicines</NavLink>
        <NavLink className="nav__link" to="/schedules">Schedules</NavLink>
        <NavLink className="nav__link" to="/analytics">Analytics</NavLink>
        {auth?.user ? (
          <button className="nav__link" type="button" onClick={auth.logout}>Logout</button>
        ) : (
          <NavLink className="nav__link" to="/login">Login</NavLink>
        )}
      </nav>
    </header>
  )
}
