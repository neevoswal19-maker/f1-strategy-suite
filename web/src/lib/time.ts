import { useEffect, useState } from 'react'

/** Re-renders every `ms` and returns Date.now(). */
export function useNow(ms = 1000) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const t = window.setInterval(() => setNow(Date.now()), ms)
    return () => window.clearInterval(t)
  }, [ms])
  return now
}

export function parts(msLeft: number) {
  const s = Math.max(0, Math.floor(msLeft / 1000))
  return { d: Math.floor(s / 86400), h: Math.floor((s % 86400) / 3600), m: Math.floor((s % 3600) / 60), s: s % 60 }
}

export function countdown(msLeft: number) {
  const { d, h, m, s } = parts(msLeft)
  if (d > 0) return `${d}d ${h}h ${String(m).padStart(2, '0')}m`
  if (h > 0) return `${h}h ${String(m).padStart(2, '0')}m`
  return `${m}m ${String(s).padStart(2, '0')}s`
}

const dayFmt = new Intl.DateTimeFormat(undefined, { weekday: 'short', day: 'numeric', month: 'short' })
const timeFmt = new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' })
const dateFmt = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' })

export const fmtDay = (iso: string) => dayFmt.format(new Date(iso))
export const fmtTime = (iso: string) => timeFmt.format(new Date(iso))
export const fmtDate = (iso: string) => dateFmt.format(new Date(iso))
export const fmtWhen = (iso: string) => `${fmtDay(iso)}, ${fmtTime(iso)}`

export const pct = (p: number, digits = 1) => `${(p * 100).toFixed(digits)}%`

export const SESSION_SHORT: Record<string, string> = {
  FP1: 'FP1', FP2: 'FP2', FP3: 'FP3', 'Sprint Qualifying': 'SQ', Sprint: 'SPR', Qualifying: 'QUALI', Race: 'RACE',
}

export function usePrefersReducedMotion() {
  const [reduced, setReduced] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const on = () => setReduced(mq.matches)
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [])
  return reduced
}
