import { useEffect, useState } from 'react'

// Re-render every second (for countdowns).
export function useNow(intervalMs = 1000) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), intervalMs)
    return () => clearInterval(t)
  }, [intervalMs])
  return now
}

// Seconds left, given the server's value and when we received it.
export function remaining(secondsLeft, receivedAt, now) {
  return Math.max(0, Math.round(secondsLeft - (now - receivedAt) / 1000))
}

export function fmtCountdown(s) {
  const m = Math.floor(s / 60)
  return `${m}:${String(s % 60).padStart(2, '0')}`
}

export const pct = (v, digits = 0) => (v == null ? '–' : `${(v * 100).toFixed(digits)}%`)
