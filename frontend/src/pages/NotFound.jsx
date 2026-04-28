import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="hero">
      <span className="hero__eyebrow">404</span>
      <h1>Page not found</h1>
      <p>The page you requested does not exist.</p>
      <Link className="btn btn--primary" to="/">Return home</Link>
    </section>
  )
}
