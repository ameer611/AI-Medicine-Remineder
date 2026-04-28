import { useEffect, useRef, useState } from 'react'

export function usePolling(task, intervalMs, enabled = true, timeoutMs = 10 * 60 * 1000) {
  const [result, setResult] = useState(null)
  const [running, setRunning] = useState(false)
  const timeoutRef = useRef(null)

  useEffect(() => {
    if (!enabled) return
    let cancelled = false
    setRunning(true)

    const tick = async () => {
      try {
        const value = await task()
        if (!cancelled) setResult(value)
      } catch (_) {
        // ignore poll errors; caller decides how to handle
      }
    }

    tick()
    const intervalId = setInterval(tick, intervalMs)
    timeoutRef.current = setTimeout(() => {
      if (!cancelled) setRunning(false)
      clearInterval(intervalId)
    }, timeoutMs)

    return () => {
      cancelled = true
      clearInterval(intervalId)
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [task, intervalMs, enabled, timeoutMs])

  return { result, running, setResult, setRunning }
}
