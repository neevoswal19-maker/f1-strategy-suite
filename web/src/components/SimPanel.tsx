import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { AnimatePresence, LayoutGroup, motion } from 'motion/react'
import { ArrowCounterClockwise, FastForward, FlagCheckered, Sliders, X, Warning, CloudRain, Siren, Wrench } from '@phosphor-icons/react'
import type { DriverCard, ParamKey, Prediction, Track, Weekend } from '../lib/types'
import type { RaceTrace, SimConfig, SimDriver, SimSummary } from '../lib/sim'
import { pct, usePrefersReducedMotion } from '../lib/time'
import ClickSpark from './bits/ClickSpark'
import DriverPhoto from './DriverPhoto'
import LockedButton from './LockedButton'
import SectionHead from './SectionHead'
import TrackMap, { type TrackMapHandle } from './TrackMap'

const N_SIMS = 1500
const LAP_TIME = 88

interface Result { featured: RaceTrace; summary: SimSummary | null }
type Reply = { id: number; featured?: RaceTrace; summary?: SimSummary }

/** Posts a job to the simulator worker; the featured race and the batch summary come back separately. */
function useSimWorker() {
  const worker = useRef<Worker | null>(null)
  const latest = useRef(0)
  const handlers = useRef<{ featured: (t: RaceTrace) => void; summary: (s: SimSummary) => void } | null>(null)
  useEffect(() => {
    const w = new Worker(new URL('../lib/sim.worker.ts', import.meta.url), { type: 'module' })
    w.onmessage = (e: MessageEvent<Reply>) => {
      if (e.data.id !== latest.current || !handlers.current) return   // a newer run replaced this one
      if (e.data.featured) handlers.current.featured(e.data.featured)
      if (e.data.summary) handlers.current.summary(e.data.summary)
    }
    worker.current = w
    return () => w.terminate()
  }, [])
  return useCallback(
    (drivers: SimDriver[], cfg: SimConfig, seed: number, featured: (t: RaceTrace) => void, summary: (s: SimSummary) => void) => {
      latest.current += 1
      handlers.current = { featured, summary }
      worker.current?.postMessage({ id: latest.current, drivers, cfg, n: N_SIMS, seed })
    },
    [],
  )
}

/* ---------------- timing tower ---------------- */
function Tower({ trace, lap, drivers }: { trace: RaceTrace; lap: number; drivers: Record<string, DriverCard> }) {
  const pos = trace.pos[Math.min(lap, trace.pos.length - 1)]
  const gap = trace.gap[Math.min(lap, trace.gap.length - 1)]
  const rows = trace.codes.map((c, i) => ({ c, p: pos[i], g: gap[i], i })).sort((a, b) => a.p - b.p)
  const grid = trace.pos[0]
  return (
    <LayoutGroup>
      <ol className="divide-y divide-line/70 border border-line bg-soft text-sm" aria-label={`Order after lap ${lap}`}>
        {rows.map(r => {
          const d = drivers[r.c]
          const gained = grid[r.i] - r.p
          const out = Number.isNaN(r.g)
          return (
            <motion.li
              layout="position"
              key={r.c}
              transition={{ type: 'spring', stiffness: 380, damping: 34 }}
              className={`grid h-[30px] grid-cols-[26px_4px_minmax(0,1fr)_auto_30px] items-center gap-2 px-2 ${out ? 'opacity-40' : ''}`}
            >
              <span className="num text-right text-muted">{r.p}</span>
              <span className="h-4 w-1" style={{ background: d?.colour ?? '#888' }} />
              <span className="truncate font-display text-[15px] font-semibold uppercase tracking-wide text-ink">{d?.last ?? r.c}</span>
              <span className="num text-xs text-body">
                {out ? 'OUT' : r.p === 1 ? (lap === 0 ? 'GRID' : 'LEADER') : `+${r.g.toFixed(1)}`}
              </span>
              <span className={`num text-right text-[11px] ${gained > 0 ? 'text-go' : gained < 0 ? 'text-red' : 'text-muted'}`}>
                {lap === 0 || out ? '' : gained > 0 ? `▲${gained}` : gained < 0 ? `▼${-gained}` : '–'}
              </span>
            </motion.li>
          )
        })}
      </ol>
    </LayoutGroup>
  )
}

/* ---------------- engineer drawer ---------------- */
function Drawer({
  open, onClose, weights, setWeights, defaults, params, rain, setRain, defaultRain, pred, drivers,
}: {
  open: boolean
  onClose: () => void
  weights: Record<ParamKey, number>
  setWeights: (w: Record<ParamKey, number>) => void
  defaults: Record<ParamKey, number>
  params: Weekend['simulator']['params']
  rain: number
  setRain: (r: number) => void
  defaultRain: number
  pred: Prediction
  drivers: Record<string, DriverCard>
}) {
  const max = Math.max(8, ...Object.values(defaults).map(v => Math.ceil(v * 2)))
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div className="fixed inset-0 z-40 bg-black/60" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} />
          <motion.aside
            role="dialog"
            aria-modal="true"
            aria-label="Engineer mode"
            className="fixed inset-y-0 right-0 z-50 flex w-full max-w-[460px] flex-col border-l border-line bg-canvas"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', stiffness: 260, damping: 32 }}
          >
            <div className="kerb" />
            <div className="flex items-center justify-between border-b border-line px-5 py-4">
              <h3 className="text-3xl">Engineer mode</h3>
              <button onClick={onClose} className="grid size-11 place-items-center rounded-full bg-card text-ink hover:bg-raised" aria-label="Close engineer mode">
                <X size={18} weight="bold" />
              </button>
            </div>
            <div className="flex-1 space-y-6 overflow-y-auto px-5 py-6">
              <p className="text-sm">
                Each factor is rated 0 to 1 per driver, 1 being the best on the grid. The weights decide how much each
                factor turns into race pace. Defaults were fitted on past races.
              </p>
              <div>
                <div className="flex items-baseline justify-between">
                  <label htmlFor="rain" className="label text-ink">Rain chance</label>
                  <span className="num text-ink">{Math.round(rain * 100)}%</span>
                </div>
                <input id="rain" type="range" min={0} max={1} step={0.05} value={rain} onChange={e => setRain(+e.target.value)} className="mt-2 w-full accent-[#e0362c]" />
              </div>
              {params.map(p => {
                const leader = [...pred.results].sort((a, b) => b.ratings[p.key] - a.ratings[p.key])[0]
                return (
                  <div key={p.key}>
                    <div className="flex items-baseline justify-between gap-3">
                      <label htmlFor={`w-${p.key}`} className="label text-ink">{p.label}</label>
                      <span className="num text-ink">{weights[p.key].toFixed(1)}</span>
                    </div>
                    <input
                      id={`w-${p.key}`}
                      type="range"
                      min={0}
                      max={max}
                      step={0.1}
                      value={weights[p.key]}
                      onChange={e => setWeights({ ...weights, [p.key]: +e.target.value })}
                      className="mt-2 w-full accent-[#e0362c]"
                      aria-describedby={`d-${p.key}`}
                    />
                    <p id={`d-${p.key}`} className="mt-1 text-xs text-muted">
                      {p.desc} Best: {drivers[leader.code]?.last ?? leader.code} ({leader.raw[p.key]}).
                    </p>
                  </div>
                )
              })}
            </div>
            <div className="flex gap-3 border-t border-line p-5">
              <button
                className="btn btn-ghost flex-1"
                onClick={() => {
                  setWeights(defaults)
                  setRain(defaultRain)
                }}
              >
                <ArrowCounterClockwise size={16} weight="bold" /> Reset
              </button>
              <button className="btn btn-red flex-1" onClick={onClose}>Done</button>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  )
}

/* ---------------- results ---------------- */
function Results({ summary, pred, drivers }: { summary: SimSummary; pred: Prediction; drivers: Record<string, DriverCard> }) {
  const rows = Object.entries(summary.win).sort((a, b) => b[1] - a[1]).slice(0, 10)
  const max = Math.max(...rows.map(r => summary.podium[r[0]]))
  const model = Object.fromEntries(pred.results.map(r => [r.code, r.win]))
  return (
    <div className="mt-12">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-4">
        <h3 className="text-3xl">{summary.n.toLocaleString()} simulated races</h3>
        <p className="num text-xs text-muted">
          rain in {pct(summary.wetShare, 0)} · safety car in {pct(summary.scShare, 0)}
        </p>
      </div>
      <ol className="divide-y divide-line border-y border-line">
        {rows.map(([code, w], i) => (
          <motion.li
            key={code}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04, type: 'spring', stiffness: 140, damping: 22 }}
            className="grid grid-cols-[36px_minmax(0,1fr)_64px] items-center gap-3 py-2.5 sm:grid-cols-[36px_160px_minmax(0,1fr)_72px_96px] sm:gap-4"
          >
            <DriverPhoto driver={drivers[code]} code={code} size={36} />
            <span className="truncate font-display text-lg font-semibold uppercase text-ink">{drivers[code]?.last ?? code}</span>
            <div className="relative col-span-2 col-start-2 row-start-2 h-3 bg-soft sm:col-span-1 sm:col-start-auto sm:row-start-auto" aria-hidden>
              <motion.div className="absolute inset-y-0 left-0 bg-line-strong" initial={{ width: 0 }} animate={{ width: `${(summary.podium[code] / max) * 100}%` }} transition={{ duration: 0.8, delay: 0.1 + i * 0.04 }} />
              <motion.div className="absolute inset-y-0 left-0" style={{ background: drivers[code]?.colour ?? '#e0362c' }} initial={{ width: 0 }} animate={{ width: `${(w / max) * 100}%` }} transition={{ duration: 0.8, delay: 0.15 + i * 0.04 }} />
            </div>
            <span className="num col-start-3 row-start-1 text-right text-ink sm:col-start-auto sm:row-start-auto">{pct(w)}</span>
            <span className="num hidden text-right text-xs text-muted sm:block">model {pct(model[code] ?? 0)}</span>
          </motion.li>
        ))}
      </ol>
    </div>
  )
}

/* ---------------- panel ---------------- */
export default function SimPanel({ weekend, track }: { weekend: Weekend; track: Track | null }) {
  const pred = weekend.prediction.gp
  const defaults = weekend.simulator.weights
  const [weights, setWeights] = useState(defaults)
  const [rain, setRain] = useState(pred?.rainChance ?? 0.15)
  const [drawer, setDrawer] = useState(false)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState<Result | null>(null)
  const [lap, setLap] = useState(0)
  const [playing, setPlaying] = useState(false)
  const mapRef = useRef<TrackMapHandle>(null)
  const raf = useRef(0)
  const reduced = usePrefersReducedMotion()
  const run = useSimWorker()

  useEffect(() => {
    setWeights(defaults)
    setRain(pred?.rainChance ?? 0.15)
    setResult(null)
    setLap(0)
  }, [weekend.id]) // eslint-disable-line react-hooks/exhaustive-deps

  const simDrivers: SimDriver[] = useMemo(
    () => (pred ? pred.results.map(r => ({ code: r.code, grid: r.qPos, ratings: r.ratings })) : []),
    [pred],
  )
  const cars = useMemo(
    () => simDrivers.map(d => ({ code: d.code, colour: weekend.drivers[d.code]?.colour ?? '#888' })),
    [simDrivers, weekend.drivers],
  )

  const stop = () => {
    cancelAnimationFrame(raf.current)
    setPlaying(false)
  }

  const play = useCallback((trace: RaceTrace) => {
    cancelAnimationFrame(raf.current)
    const lapMs = Math.min(420, Math.max(260, 24000 / trace.laps))
    const start = performance.now()
    setPlaying(true)
    let shown = -1
    const tick = (now: number) => {
      const f = Math.min((now - start) / lapMs, trace.laps)
      const k = Math.floor(f)
      const frac = f - k
      if (k !== shown) {
        shown = k
        setLap(k)
      }
      const a = trace.gap[k]
      const b = trace.gap[Math.min(k + 1, trace.laps)]
      const progress: Record<string, number> = {}
      trace.codes.forEach((c, i) => {
        const g = Number.isNaN(b[i]) ? NaN : a[i] + (b[i] - a[i]) * frac
        progress[c] = f - g / LAP_TIME
      })
      mapRef.current?.place(progress)
      if (f < trace.laps) raf.current = requestAnimationFrame(tick)
      else setPlaying(false)
    }
    raf.current = requestAnimationFrame(tick)
  }, [])

  useEffect(() => () => cancelAnimationFrame(raf.current), [])

  const simulate = () => {
    if (!pred) return
    stop()
    setBusy(true)
    const cfg: SimConfig = {
      weights, rainChance: rain, laps: weekend.circuit.laps, overtaking: weekend.circuit.overtaking,
      scChance: weekend.circuit.scChance, pitLoss: weekend.circuit.pitLoss ?? 22, lapTime: LAP_TIME,
    }
    run(
      simDrivers,
      cfg,
      Math.floor(Math.random() * 1e9),
      featured => {
        setResult({ featured, summary: null })
        if (reduced) {
          setLap(featured.laps)
          const progress = Object.fromEntries(featured.codes.map((c, i) => [c, -featured.gap[featured.laps][i] / LAP_TIME]))
          requestAnimationFrame(() => mapRef.current?.place(progress))
        } else {
          setLap(0)
          play(featured)
        }
      },
      summary => {
        setBusy(false)
        setResult(r => (r ? { ...r, summary } : r))
      },
    )
  }

  const skip = () => {
    if (!result) return
    stop()
    const t = result.featured
    setLap(t.laps)
    mapRef.current?.place(Object.fromEntries(t.codes.map((c, i) => [c, -t.gap[t.laps][i] / LAP_TIME])))
  }

  const tuned = JSON.stringify(weights) !== JSON.stringify(defaults) || rain !== (pred?.rainChance ?? 0.15)
  const trace = result?.featured
  const events = trace ? trace.events.filter(e => e.lap <= lap).slice(-4).reverse() : []
  const finished = trace && lap >= trace.laps
  const winner = trace?.finish[0]

  return (
    <section id="simulator" className="scroll-mt-16 border-t border-line bg-soft/40">
      <div className="mx-auto max-w-[1400px] px-4 py-20 sm:px-8 lg:py-28">
        <SectionHead title="Race simulator">
          Runs the race lap by lap from the real grid: each driver's pace comes from ten factors below, cars need a
          real pace advantage to pass, everyone stops once, and safety cars, retirements and rain can all happen.
        </SectionHead>

        {!pred ? (
          <LockedButton gate={weekend.gates.gp} label="Simulate race" finished={weekend.status === 'done'} />
        ) : (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <ClickSpark sparkColor={['#e0362c', '#f4f4f5', '#ffd12e']} sparkCount={12} sparkRadius={30}>
                <button className="btn btn-red" onClick={simulate} disabled={busy} aria-busy={busy}>
                  <FlagCheckered size={18} weight="fill" />
                  {busy ? 'Simulating…' : result ? 'Simulate again' : 'Simulate race'}
                </button>
              </ClickSpark>
              <button className="btn btn-ghost" onClick={() => setDrawer(true)}>
                <Sliders size={18} weight="bold" /> Engineer mode{tuned && <span className="size-2 rounded-full bg-amber" aria-label="custom settings" />}
              </button>
              {playing && (
                <button className="btn btn-ghost" onClick={skip}>
                  <FastForward size={18} weight="bold" /> Skip to flag
                </button>
              )}
            </div>

            {/* parameter strip */}
            <div className="mt-8 flex flex-wrap gap-2">
              {weekend.simulator.params.map(p => (
                <span key={p.key} className="border border-line px-3 py-1.5 text-xs text-body" title={p.desc}>
                  {p.label} <span className="num ml-1 text-ink">{weights[p.key].toFixed(1)}</span>
                </span>
              ))}
            </div>

            <div className="mt-10 grid gap-6 lg:grid-cols-[minmax(0,7fr)_minmax(300px,4fr)]">
              <div className="relative min-h-[320px] border border-line bg-canvas p-4 sm:p-6">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="label">Lap</p>
                    <p className="num text-4xl font-semibold text-ink">
                      {trace ? Math.max(lap, 0) : 0}
                      <span className="text-xl text-muted">/{trace?.laps ?? weekend.circuit.laps}</span>
                    </p>
                  </div>
                  <div className="flex flex-col items-end gap-1 text-xs">
                    {trace?.scLaps.includes(lap) && <span className="label flex items-center gap-1.5 bg-amber px-2 py-1 text-canvas"><Siren size={14} weight="fill" />Safety car</span>}
                    {trace?.rainFrom && lap >= trace.rainFrom && <span className="label flex items-center gap-1.5 bg-[#0067ad] px-2 py-1 text-white"><CloudRain size={14} weight="fill" />Wet</span>}
                  </div>
                </div>
                <TrackMap ref={mapRef} track={track} cars={trace ? cars : []} className="mx-auto mt-2 h-[300px] w-full sm:h-[420px]" />
                <ul className="mt-3 min-h-[84px] space-y-1 text-sm" aria-live="polite">
                  {!trace && <li className="text-muted">Press Simulate race to start from the real grid.</li>}
                  {events.map((e, i) => (
                    <li key={`${e.lap}-${e.text}`} className={`flex gap-3 ${i ? 'text-muted' : 'text-ink'}`}>
                      <span className="num w-10 text-muted">L{e.lap}</span>
                      {e.kind === 'dnf' ? <Warning size={16} className="text-red" /> : e.kind === 'sc' ? <Siren size={16} className="text-amber" /> : e.kind === 'pit' ? <Wrench size={16} /> : null}
                      {e.text}
                    </li>
                  ))}
                </ul>
                <AnimatePresence>
                  {finished && winner && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className="absolute inset-x-4 bottom-4 flex items-center gap-4 border border-line-strong bg-canvas/95 p-3 backdrop-blur sm:inset-x-6"
                    >
                      <div className="checker h-12 w-12 shrink-0 bg-canvas" aria-hidden />
                      <DriverPhoto driver={weekend.drivers[winner]} code={winner} size={48} />
                      <div className="min-w-0">
                        <p className="label">Chequered flag</p>
                        <p className="truncate font-display text-2xl font-bold uppercase text-ink">
                          {weekend.drivers[winner]?.last ?? winner} wins this one
                        </p>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              <div>
                {trace ? (
                  <Tower trace={trace} lap={lap} drivers={weekend.drivers} />
                ) : (
                  <div className="grid h-full min-h-[320px] place-items-center border border-dashed border-line p-6 text-center text-sm text-muted">
                    The timing tower fills in once the lights go out.
                  </div>
                )}
              </div>
            </div>

            {result?.summary && finished && <Results summary={result.summary} pred={pred} drivers={weekend.drivers} />}

            <Drawer
              open={drawer}
              onClose={() => setDrawer(false)}
              weights={weights}
              setWeights={setWeights}
              defaults={defaults}
              params={weekend.simulator.params}
              rain={rain}
              setRain={setRain}
              defaultRain={pred.rainChance}
              pred={pred}
              drivers={weekend.drivers}
            />
          </>
        )}
      </div>
    </section>
  )
}
