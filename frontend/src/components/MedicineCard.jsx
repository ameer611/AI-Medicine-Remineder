export default function MedicineCard({ medication, children }) {
  return (
    <article className="card stack">
      <div>
        <span className="status-pill">{medication.name}</span>
        <h3>{medication.dosage_per_day} dose(s) per day</h3>
        <p className="muted">Times: {medication.times?.join(', ') || '—'}</p>
      </div>
      {children}
    </article>
  )
}
