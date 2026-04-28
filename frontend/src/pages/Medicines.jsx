import { useState } from 'react'
import { parsePrescription, saveMedication, uploadImage } from '../api/medicines'
import LoadingSpinner from '../components/LoadingSpinner'
import { useAuth } from '../hooks/useAuth'

export default function Medicines() {
  const auth = useAuth()
  const [ocrText, setOcrText] = useState('')
  const [parsed, setParsed] = useState([])
  const [manual, setManual] = useState({ name: '', dosage_per_day: 1, notes: '', suggested_times: '' })
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  const onUpload = async event => {
    const file = event.target.files?.[0]
    if (!file) return
    setBusy(true)
    setMessage('')
    try {
      const ocr = await uploadImage(file)
      setOcrText(ocr.text || '')
      const result = await parsePrescription(ocr.text || '')
      setParsed(result.medications || [])
    } catch (error) {
      setMessage('Failed to process the prescription image.')
    } finally {
      setBusy(false)
    }
  }

  const saveParsed = async medication => {
    await saveMedication({
      telegram_id: auth.user.telegram_id,
      medication: {
        name: medication.name,
        dosage_per_day: medication.dosage_per_day,
        timing: medication.timing || 'custom',
        notes: medication.notes || null,
        user_id: auth.user.id,
      },
      times: medication.suggested_times || [],
      reminder_offset_minutes: 10,
      duration_in_days: medication.duration_in_days || 7,
    })
    setMessage(`Saved ${medication.name}`)
  }

  const saveManual = async () => {
    const times = manual.suggested_times.split(',').map(item => item.trim()).filter(Boolean)
    await saveMedication({
      telegram_id: auth.user.telegram_id,
      medication: {
        name: manual.name,
        dosage_per_day: Number(manual.dosage_per_day),
        timing: 'custom',
        notes: manual.notes || null,
        user_id: auth.user.id,
      },
      times,
      reminder_offset_minutes: 10,
      duration_in_days: 7,
    })
    setMessage(`Saved ${manual.name}`)
  }

  if (busy) return <LoadingSpinner label="Scanning prescription..." />

  return (
    <section className="stack">
      <div className="hero">
        <span className="hero__eyebrow">Prescription intake</span>
        <h1>Add medicines from image or manually.</h1>
        <p>Upload a prescription image, review OCR and parsed medications, and save with suggested times.</p>
      </div>

      <div className="card stack">
        <h3>Upload prescription</h3>
        <input type="file" accept="image/*" onChange={onUpload} />
        {ocrText ? <div className="panel"><pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{ocrText}</pre></div> : null}
      </div>

      {parsed.length ? (
        <div className="grid grid--2">
          {parsed.map(med => (
            <div className="card stack" key={med.name}>
              <div>
                <span className="status-pill">{med.name}</span>
                <h3>{med.dosage_per_day} doses/day</h3>
                <p className="muted">Suggested times: {(med.suggested_times || []).join(', ') || '—'}</p>
                <p className="muted">Reason: {med.timing_reasoning || '—'}</p>
              </div>
              <button className="btn btn--primary" type="button" onClick={() => saveParsed(med)}>Confirm & Save</button>
            </div>
          ))}
        </div>
      ) : null}

      <div className="card stack">
        <h3>Add manually</h3>
        <div className="grid grid--2">
          <label className="field"><span>Name</span><input value={manual.name} onChange={e => setManual({ ...manual, name: e.target.value })} /></label>
          <label className="field"><span>Doses/day</span><input type="number" min="1" max="4" value={manual.dosage_per_day} onChange={e => setManual({ ...manual, dosage_per_day: e.target.value })} /></label>
        </div>
        <label className="field"><span>Notes</span><textarea value={manual.notes} onChange={e => setManual({ ...manual, notes: e.target.value })} /></label>
        <label className="field"><span>Times (comma separated HH:MM)</span><input value={manual.suggested_times} onChange={e => setManual({ ...manual, suggested_times: e.target.value })} /></label>
        <div className="actions"><button className="btn btn--primary" type="button" onClick={saveManual}>Save manually</button></div>
      </div>

      {message ? <div className="empty">{message}</div> : null}
    </section>
  )
}
