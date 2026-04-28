export default function LoadingSpinner({ label = 'Loading...' }) {
  return (
    <div className="hero" style={{ placeItems: 'center', textAlign: 'center' }}>
      <div className="spinner" />
      <p className="muted">{label}</p>
    </div>
  )
}
