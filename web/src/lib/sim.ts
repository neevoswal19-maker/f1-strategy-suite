import type { ParamKey } from './types'

/*
 * Lap-by-lap race simulator.
 *
 * Each driver's strength is the weighted sum of their 0-1 ratings (weights fitted on past races by the
 * pipeline, adjustable in Engineer mode). On race day that strength gets Gumbel noise, which is what the
 * conditional-logit fit assumes, and becomes a pace advantage in seconds per lap. Cars start in grid
 * order, can only pass when they are quicker by more than the circuit's overtaking threshold, make one
 * pit stop, can retire, and get bunched up by safety cars. Rain adds noise and turns on wet-weather skill.
 */

export interface SimDriver {
  code: string
  grid: number
  ratings: Record<ParamKey, number>
}

export interface SimConfig {
  weights: Record<ParamKey, number>
  rainChance: number
  laps: number
  overtaking: number      // 0 = easy to pass, 1 = processional
  scChance: number
  pitLoss: number
  lapTime: number
}

export interface RaceTrace {
  laps: number
  codes: string[]                 // driver order used by the arrays below
  pos: number[][]                 // [lap][driver] position (1-based), lap 0 = grid
  gap: number[][]                 // [lap][driver] seconds behind the leader
  dnfLap: (number | null)[]
  pitLap: number[]
  scLaps: number[]
  rainFrom: number | null
  finish: string[]
  events: { lap: number; kind: 'sc' | 'dnf' | 'rain' | 'pass' | 'pit'; text: string }[]
}

export interface SimSummary {
  n: number
  win: Record<string, number>
  podium: Record<string, number>
  avgPos: Record<string, number>
  dnf: Record<string, number>
  wetShare: number
  scShare: number
}

const PACE_K = 0.16          // seconds per lap for one unit of strength
const GRID_GAP = 0.32        // seconds between grid slots at the start
const MIN_GAP = 0.3          // a car stuck behind another stays this far back
const SC_PACE = 1.4

export function rng(seed: number) {
  let a = seed >>> 0
  const next = () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
  return {
    next,
    normal: () => {
      const u = Math.max(next(), 1e-12)
      return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * next())
    },
    gumbel: () => -Math.log(-Math.log(Math.max(next(), 1e-12))),
  }
}

export function strength(d: SimDriver, w: Record<ParamKey, number>, wet: boolean) {
  let s = 0
  for (const k of Object.keys(w) as ParamKey[]) {
    if (k === 'wet_skill' && !wet) continue
    s += (w[k] ?? 0) * (d.ratings[k] ?? 0.5)
  }
  return s
}

export interface Outcome { finish: string[]; raining: boolean; sc: boolean; dnfs: string[] }

export function simulateRace(drivers: SimDriver[], cfg: SimConfig, seed: number, trace = false): RaceTrace | Outcome {
  const R = rng(seed)
  const n = drivers.length
  const L = Math.max(10, cfg.laps)
  const raining = R.next() < cfg.rainChance
  const rainFrom = raining ? (R.next() < 0.5 ? 1 : 1 + Math.floor(R.next() * L * 0.6)) : null

  const form = drivers.map(d => strength(d, cfg.weights, raining) + R.gumbel() * (raining ? 1.5 : 1))
  const best = Math.max(...form)
  const pace = form.map(f => cfg.lapTime - PACE_K * (f - best))
  const reliability = drivers.map(d => d.ratings.reliability ?? 0.5)
  const dnfLap = drivers.map((_, i) => {
    const p = 0.025 + 0.09 * (1 - reliability[i]) + (raining ? 0.04 : 0)
    return R.next() < p ? 1 + Math.floor(R.next() * (L - 1)) : null
  })
  const pitLap = drivers.map(() => Math.round(L * (0.33 + R.next() * 0.3)))
  const scStart = R.next() < cfg.scChance ? Math.max(2, Math.round(L * (0.12 + R.next() * 0.7))) : null
  const scLaps = scStart ? [scStart, scStart + 1, scStart + 2, scStart + 3].filter(l => l <= L) : []
  const threshold = 0.12 + 0.9 * cfg.overtaking

  // grid: cumulative time offset by slot, plus a messy first lap
  const gridOrder = drivers.map((_, i) => i).sort((a, b) => drivers[a].grid - drivers[b].grid)
  const t = new Array<number>(n).fill(0)
  gridOrder.forEach((i, slot) => (t[i] = slot * GRID_GAP))
  let order = gridOrder.slice()
  const out = new Array<boolean>(n).fill(false)

  const posHist: number[][] = []
  const gapHist: number[][] = []
  const events: RaceTrace['events'] = []
  const snapshot = () => {
    if (!trace) return
    const p = new Array<number>(n).fill(n)
    const g = new Array<number>(n).fill(0)
    const lead = t[order[0]]
    order.forEach((i, k) => {
      p[i] = k + 1
      g[i] = t[i] - lead
    })
    const gone = drivers.map((_, i) => i).filter(i => out[i])
    gone.forEach((i, k) => {
      p[i] = order.length + k + 1
      g[i] = NaN
    })
    posHist.push(p)
    gapHist.push(g)
  }
  snapshot()
  if (trace && rainFrom === 1) events.push({ lap: 1, kind: 'rain', text: 'Wet start' })

  for (let lap = 1; lap <= L; lap++) {
    const underSC = scLaps.includes(lap)
    const wetNow = rainFrom !== null && lap >= rainFrom
    if (trace && lap === rainFrom && lap > 1) events.push({ lap, kind: 'rain', text: 'Rain starts to fall' })
    if (trace && lap === scStart) events.push({ lap, kind: 'sc', text: 'Safety car deployed' })

    // lap times
    const lapT = new Array<number>(n).fill(0)
    const pitted = new Array<boolean>(n).fill(false)
    for (const i of order) {
      let x = underSC ? cfg.lapTime * SC_PACE : pace[i] + R.normal() * (wetNow ? 0.55 : 0.22)
      if (wetNow && !underSC) x *= 1.07
      if (lap === 1) x += Math.abs(R.normal()) * 0.6
      if (lap === pitLap[i]) {
        const loss = cfg.pitLoss + R.normal() * 0.8 + (R.next() < 0.05 ? 3 : 0)
        x += underSC ? loss * 0.5 : loss
        pitted[i] = true
      }
      lapT[i] = x
    }

    // apply in running order: a faster car only gets by if it is quick enough to pass here
    const prev = order.slice()
    const next = t.slice()
    let passes = 0
    for (let k = 0; k < prev.length; k++) {
      const i = prev[k]
      let ti = t[i] + lapT[i]
      if (k > 0 && !underSC && !pitted[i]) {
        const a = prev[k - 1]
        const ta = next[a]          // where the car ahead ends this lap (already resolved)
        if (!pitted[a] && ti < ta + MIN_GAP) {
          const edge = lapT[a] - lapT[i]
          if (edge > threshold * (0.6 + R.next() * 0.8)) passes++
          else ti = Math.max(ti, ta + MIN_GAP + R.next() * 0.15)
        }
      }
      next[i] = ti
    }
    for (const i of prev) t[i] = next[i]

    // retirements
    for (const i of order) {
      if (dnfLap[i] === lap) {
        out[i] = true
        if (trace) events.push({ lap, kind: 'dnf', text: `${drivers[i].code} retires` })
      }
    }
    order = order.filter(i => !out[i]).sort((a, b) => t[a] - t[b])

    // safety car ends: field bunched up behind the leader
    if (scLaps.length && lap === scLaps[scLaps.length - 1]) {
      const lead = t[order[0]]
      order.forEach((i, k) => (t[i] = lead + k * 0.4))
      if (trace) events.push({ lap, kind: 'sc', text: 'Safety car in, racing resumes' })
    }
    if (trace && passes >= 3 && lap > 1 && !underSC) events.push({ lap, kind: 'pass', text: `${passes} overtakes` })
    snapshot()
  }

  const retired = drivers.map((_, i) => i).filter(i => out[i]).sort((a, b) => (dnfLap[b] ?? 0) - (dnfLap[a] ?? 0))
  const finish = [...order, ...retired].map(i => drivers[i].code)
  if (!trace) return { finish, raining, sc: scStart !== null, dnfs: retired.map(i => drivers[i].code) }
  return {
    laps: L, codes: drivers.map(d => d.code), pos: posHist, gap: gapHist, dnfLap, pitLap,
    scLaps, rainFrom, finish, events,
  }
}

export function runMany(drivers: SimDriver[], cfg: SimConfig, n: number, seed: number): SimSummary {
  const win: Record<string, number> = {}
  const podium: Record<string, number> = {}
  const sumPos: Record<string, number> = {}
  const dnf: Record<string, number> = {}
  for (const d of drivers) {
    win[d.code] = podium[d.code] = sumPos[d.code] = dnf[d.code] = 0
  }
  let wet = 0
  let sc = 0
  for (let s = 0; s < n; s++) {
    const { finish, raining, sc: hadSC, dnfs } = simulateRace(drivers, cfg, seed + s * 7919) as Outcome
    if (raining) wet++
    if (hadSC) sc++
    dnfs.forEach(c => dnf[c]++)
    finish.forEach((c, k) => {
      if (k === 0) win[c]++
      if (k < 3) podium[c]++
      sumPos[c] += k + 1
    })
  }
  const avgPos: Record<string, number> = {}
  for (const d of drivers) {
    win[d.code] /= n
    podium[d.code] /= n
    avgPos[d.code] = sumPos[d.code] / n
    dnf[d.code] /= n
  }
  return { n, win, podium, avgPos, dnf, wetShare: wet / n, scShare: sc / n }
}
