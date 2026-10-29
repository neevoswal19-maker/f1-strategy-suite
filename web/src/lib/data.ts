import { useEffect, useState } from 'react'
import type { Index, SeasonSummary, Track, Weekend } from './types'

const BASE = `${import.meta.env.BASE_URL}data/`

async function getJSON<T>(path: string): Promise<T> {
  // the cron job updates data during race weekends, so skip the browser cache for it
  const res = await fetch(BASE + path, { cache: 'no-cache' })
  if (!res.ok) throw new Error(`${res.status} loading ${path}`)
  return res.json() as Promise<T>
}

type State<T> = { data: T | null; error: string | null; loading: boolean }

function useJSON<T>(path: string | null, refreshMs = 0): State<T> {
  const [state, setState] = useState<State<T>>({ data: null, error: null, loading: !!path })
  useEffect(() => {
    if (!path) return
    let alive = true
    setState(s => ({ ...s, loading: true, error: null }))
    getJSON<T>(path)
      .then(data => alive && setState({ data, error: null, loading: false }))
      .catch(err => alive && setState({ data: null, error: String(err.message ?? err), loading: false }))
    // background refresh keeps the old data on screen and ignores failures
    const timer = refreshMs
      ? window.setInterval(() => {
          getJSON<T>(path).then(data => alive && setState({ data, error: null, loading: false })).catch(() => {})
        }, refreshMs)
      : 0
    return () => {
      alive = false
      if (timer) window.clearInterval(timer)
    }
  }, [path, refreshMs])
  return state
}

export const useIndex = () => useJSON<Index>('index.json', 10 * 60_000)
export const useWeekend = (id: string | null, refreshMs = 0) =>
  useJSON<Weekend>(id ? `weekends/${id}.json` : null, refreshMs)
export const useTrack = (file: string | null) => useJSON<Track>(file)
export const useSeason = (season: number | null) => useJSON<SeasonSummary>(season ? `seasons/${season}.json` : null)

/** Weekend id from the URL hash (#/2026-18), so archive pages can be linked. */
export function useHashWeekend(): [string | null, (id: string | null) => void] {
  const read = () => {
    const m = window.location.hash.match(/#\/(\d{4}-\d{2})/)
    return m ? m[1] : null
  }
  const [id, setId] = useState<string | null>(read)
  useEffect(() => {
    const on = () => setId(read())
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  const go = (next: string | null) => {
    window.location.hash = next ? `/${next}` : ''
    setId(next)
  }
  return [id, go]
}
