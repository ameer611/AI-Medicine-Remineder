export default function IntakeButtons({ onAction, disabled = false }) {
  return (
    <div className="actions">
      <button className="btn btn--primary" type="button" disabled={disabled} onClick={() => onAction('consumed')}>
        ✅ Taken
      </button>
      <button className="btn" type="button" disabled={disabled} onClick={() => onAction('not_consumed')}>
        ❌ Skipped
      </button>
      <button className="btn" type="button" disabled={disabled} onClick={() => onAction('felt_bad')}>
        😟 Feeling bad
      </button>
    </div>
  )
}
