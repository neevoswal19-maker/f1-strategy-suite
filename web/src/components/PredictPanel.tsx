import { useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { ArrowDown, ArrowUp, CheckCircle, XCircle, Flag } from '@phosphor-icons/react'
import type { DriverCard, Index, Prediction, Weekend } from '../lib/types'
import { pct, usePrefersReducedMotion } from '../lib/time'
import ClickSpark from './bits/ClickSpark'
import CountUp from './bits/CountUp'
import DecryptedText from './bits/DecryptedText'
import DriverPhoto from './DriverPhoto'
import LockedButton from './LockedButton'
import SectionHead from './SectionHead'

type Kind = 'gp' | 'sprint'

function LoadingLog({ pred, onDone }: { pred: Prediction; onDone: () => void }) {
  const lines = useMemo(
    () => [
      `${pred.sessions.practice}: long-run pace for ${pred.counts.drivers} drivers`,
      `${pred.sessions.qualifying}: grid order and gaps to pole`,
      `Form, reliability and track history from ${pred.counts.trainingWeekends} past weekends`,
      `Rain chance ${Math.round(pred.rainChance * 100)}% (${pred.rainSource === 'forecast' ? 'forecast' : 'no forecast, using the default'})`,
      'Sampling 20,000 finishing orders',
    ],
    [pred],
  )
  const [shown, setShown] = useState(0)
  useEffect(() => {
    if (shown >= lines.length) {
      const t = window.setTimeout(onDone, 450)
      return () => clearTimeout(t)
    }
    const t = window.setTimeout(() => setShown(s => s + 1), 430)
    return () => clearTimeout(t)
  }, [shown, lines.length, onDone])
  return (
    <div className="border border-line bg-soft p-5 sm:p-6" role="status" aria-live="polite">
      <ul className="num space-y-2 text-sm">
        {lines.slice(0, shown + 1).map((l, i) => (
          <motion.li key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} className="flex gap-3">
            <span className={i < shown ? 'text-go' : 'text-amber'}>{i < shown ? 'OK ' : '>> '}</span>
            <span className={i < shown ? 'text-body' : 'text-ink'}>{l}</span>
          </motion.li>
        ))}
      </ul>
      <div className="mt-5 h-[3px] w-full overflow-hidden bg-line">
        <motion.div
          className="h-full bg-red"
          initial={{ width: '0%' }}
          animate={{ width: `${(Math.min(shown, lines.length) / lines.length) * 100}%` }}
          transition={{ ease: [0.16, 1, 0.3, 1], duration: 0.4 }}
        />
      </div>
    </div>
  )
}

function WinnerReveal({ pred, drivers }: { pred: Prediction; drivers: Record<string, DriverCard> }) {
  const top = pred.results[0]
  const d = drivers[top.code]
  const colour = d?.colour ?? '#e0362c'
  const pros = top.reasons.filter(r => r.impact > 0).slice(0, 4)
  const con = [...top.reasons].sort((a, b) => a.impact - b.impact)[0]
  const maxImpact = Math.max(...pros.map(r => r.impact), 0.01)
  const runnerUp = pred.results[1]

  return (
    <motion.div initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.12 } } }}>
      <div className="grid gap-px bg-line lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        {/* the winner card */}
        <motion.div
          variants={{ hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } }}
          transition={{ type: 'spring', stiffness: 100, damping: 20 }}
          className="relative overflow-hidden bg-canvas"
        >
          {/* team colour over a dark base so white type keeps its contrast on light liveries */}
          <div className="absolute inset-0" style={{ background: `linear-gradient(150deg, ${colour}8c 0%, ${colour}40 40%, transparent 80%)` }} />
          <div className="absolute -right-6 top-2 font-display text-[11rem] font-extrabold leading-none text-white/10 sm:text-[14rem]" aria-hidden>
            {d?.number ?? ''}
          </div>
          <div className="relative grid grid-cols-[minmax(0,1fr)_auto] items-end gap-4 p-5 pt-8 sm:p-8">
            <div className="z-10 self-start">
              <p className="font-display text-xl font-semibold uppercase text-white/85">{d?.first}</p>
              <h3 className="text-[clamp(2.8rem,6vw,4.6rem)] text-white">
                <DecryptedText text={(d?.last ?? top.code).toUpperCase()} animateOn="view" speed={45} maxIterations={14} sequential revealDirection="start" />
              </h3>
              <p className="mt-2 text-sm text-white/85">{top.team} · predicted {pred.label} winner</p>
            </div>
            <DriverPhoto driver={d} code={top.code} size={168} plain className="-mb-5 sm:-mb-8" />
          </div>
          <div className="relative grid grid-cols-3 gap-px border-t border-white/15 bg-white/10">
            {[
              { l: 'Win', v: top.win * 100, s: '%', dec: 1 },
              { l: 'Podium', v: top.podium * 100, s: '%', dec: 0 },
              { l: 'Starts', v: top.qPos, s: '', dec: 0, p: 'P' },
            ].map(x => (
              <div key={x.l} className="bg-canvas/80 p-4 sm:p-5">
                <p className="label">{x.l}</p>
                <p className="num mt-1 text-3xl font-semibold text-white sm:text-4xl">
                  <CountUp to={x.v} decimals={x.dec} suffix={x.s} prefix={x.p ?? ''} duration={1.4} trigger="view" easing="expo" />
                </p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* why */}
        <motion.div
          variants={{ hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } }}
          transition={{ type: 'spring', stiffness: 100, damping: 20 }}
          className="bg-canvas p-5 sm:p-8"
        >
          <h3 className="text-3xl sm:text-4xl">Why {d?.last ?? top.code} wins</h3>
          <ul className="mt-6 divide-y divide-line border-y border-line">
            {pros.map((r, i) => (
              <motion.li
                key={r.key}
                initial={{ opacity: 0, x: 16 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.25 + i * 0.08, type: 'spring', stiffness: 120, damping: 20 }}
                className="grid grid-cols-[minmax(0,1fr)_88px] items-center gap-4 py-4"
              >
                <div>
                  <p className="label text-ink">{r.title}</p>
                  <p className="mt-1 text-body">{r.text}</p>
                </div>
                <div className="h-1.5 bg-line" aria-hidden>
                  <motion.div
                    className="h-full bg-go"
                    initial={{ width: 0 }}
                    whileInView={{ width: `${(r.impact / maxImpact) * 100}%` }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.4 + i * 0.08, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                  />
                </div>
              </motion.li>
            ))}
          </ul>
          {con && con.impact < 0 && (
            <div className="mt-6 flex gap-3 text-sm">
              <ArrowDown size={18} weight="bold" className="mt-0.5 shrink-0 text-red" />
              <p>
                <span className="text-ink">What could go wrong: </span>
                {con.title.toLowerCase()}. {con.text}.
              </p>
            </div>
          )}
          {runnerUp && (
            <p className="mt-3 flex gap-3 text-sm">
              <ArrowUp size={18} weight="bold" className="mt-0.5 shrink-0 text-amber" />
              <span>
                <span className="text-ink">Biggest threat: </span>
                {drivers[runnerUp.code]?.last ?? runnerUp.code} at {pct(runnerUp.win)} to win, starting P{runnerUp.qPos}.
              </span>
            </p>
          )}
          {pred.actualWinner && (
            <div className={`mt-6 flex items-center gap-3 border p-4 ${pred.hit ? 'border-go/50' : 'border-line-strong'}`}>
              {pred.hit ? <CheckCircle size={22} weight="fill" className="text-go" /> : <XCircle size={22} weight="fill" className="text-red" />}
              <p className="text-sm">
                <span className="text-ink">Actual winner: {drivers[pred.actualWinner]?.last ?? pred.actualWinner}.</span>{' '}
                {pred.hit
                  ? 'The model called it.'
                  : `The model had them at ${pct(pred.results.find(r => r.code === pred.actualWinner)?.win ?? 0)}, ranked #${pred.results.findIndex(r => r.code === pred.actualWinner) + 1}.`}
              </p>
            </div>
          )}
        </motion.div>
      </div>
    </motion.div>
  )
}

function FieldOdds({ pred, drivers }: { pred: Prediction; drivers: Record<string, DriverCard> }) {
  const [all, setAll] = useState(false)
  const rows = all ? pred.results : pred.results.slice(0, 10)
  const max = pred.results[0].podium
  return (
    <div className="mt-14">
      <div className="mb-4 flex items-end justify-between gap-4">
        <h3 className="text-3xl">The whole field</h3>
        <div className="flex items-center gap-4 text-xs text-muted">
          <span className="flex items-center gap-1.5"><span className="h-2 w-4 bg-red" />Win</span>
          <span className="flex items-center gap-1.5"><span className="h-2 w-4 bg-line-strong" />Podium</span>
        </div>
      </div>
      <ol className="divide-y divide-line border-y border-line">
        {rows.map((r, i) => {
          const d = drivers[r.code]
          return (
            <motion.li
              key={r.code}
              layout
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              viewport={{ once: true }}
              transition={{ delay: Math.min(i, 10) * 0.03 }}
              className="grid grid-cols-[28px_40px_minmax(0,1fr)_64px] items-center gap-3 py-2.5 sm:grid-cols-[32px_44px_180px_minmax(0,1fr)_72px_72px] sm:gap-4"
            >
              <span className="num text-right text-muted">{i + 1}</span>
              <DriverPhoto driver={d} code={r.code} size={40} />
              <div className="min-w-0">
                <p className="truncate font-display text-lg font-semibold uppercase text-ink">
                  <span className="mr-2 inline-block h-3 w-1 align-middle" style={{ background: d?.colour ?? '#888' }} />
                  {d?.last ?? r.code}
                </p>
                <p className="truncate text-xs text-muted">{r.team} · starts P{r.qPos}</p>
              </div>
              <div className="relative col-span-3 col-start-2 row-start-2 h-3 bg-soft sm:col-span-1 sm:col-start-auto sm:row-start-auto" aria-hidden>
                <motion.div
                  className="absolute inset-y-0 left-0 bg-line-strong"
                  initial={{ width: 0 }}
                  whileInView={{ width: `${(r.podium / max) * 100}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1], delay: 0.1 + Math.min(i, 10) * 0.03 }}
                />
                <motion.div
                  className="absolute inset-y-0 left-0 bg-red"
                  initial={{ width: 0 }}
                  whileInView={{ width: `${(r.win / max) * 100}%` }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1], delay: 0.2 + Math.min(i, 10) * 0.03 }}
                />
              </div>
              <span className="num col-start-4 row-start-1 text-right text-ink sm:col-start-auto sm:row-start-auto">{pct(r.win)}</span>
              <span className="num hidden text-right text-muted sm:block">{pct(r.podium, 0)}</span>
            </motion.li>
          )
        })}
      </ol>
      {pred.results.length > 10 && (
        <button className="btn btn-ghost mt-4 min-h-[44px] px-5 text-xs" onClick={() => setAll(a => !a)}>
          {all ? 'Show top 10' : `Show all ${pred.results.length}`}
        </button>
      )}
    </div>
  )
}

function ModelNote({ index }: { index: Index | null }) {
  if (!index) return null
  const m = index.model
  const mine = m.backtest[m.name]
  const pole = m.backtest['Pole sitter wins']
  if (!mine || !pole) return null
  return (
    <div className="mt-14 grid gap-px border border-line bg-line sm:grid-cols-3">
      <div className="bg-canvas p-5">
        <p className="label">Model</p>
        <p className="mt-2 text-ink">{m.name}</p>
        <p className="mt-1 text-sm">Trained on {m.trainingWeekends} weekends since 2023</p>
      </div>
      <div className="bg-canvas p-5">
        <p className="label">Back-test, last {m.window.races} races</p>
        <p className="num mt-2 text-2xl text-ink">{pct(mine.topPickWon, 0)} <span className="font-sans text-sm text-body">top pick won</span></p>
        <p className="num text-sm">{pct(mine.winnerInTop3, 0)} winner in its top 3</p>
      </div>
      <div className="bg-canvas p-5">
        <p className="label">Baseline</p>
        <p className="num mt-2 text-2xl text-ink">{pct(pole.topPickWon, 0)} <span className="font-sans text-sm text-body">pole sitter won</span></p>
        <p className="num text-sm">{index.hitRate.races ? `${index.hitRate.hits}/${index.hitRate.races} correct in ${index.season} so far` : ''}</p>
      </div>
    </div>
  )
}

export default function PredictPanel({ weekend, index }: { weekend: Weekend; index: Index | null }) {
  const kinds: Kind[] = weekend.sprint ? ['gp', 'sprint'] : ['gp']
  const [kind, setKind] = useState<Kind>('gp')
  const [phase, setPhase] = useState<'idle' | 'loading' | 'shown'>('idle')
  const reduced = usePrefersReducedMotion()
  const pred = weekend.prediction[kind]

  useEffect(() => setPhase('idle'), [weekend.id, kind])

  return (
    <section id="prediction" className="scroll-mt-16 mx-auto max-w-[1400px] px-4 py-20 sm:px-8 lg:py-28">
      <SectionHead title="Predicted winner">
        A model trained on every weekend since 2023 reads this weekend's practice long runs and qualifying,
        adds recent form, the car, reliability and each driver's record here, then turns it into a win chance.
      </SectionHead>

      {kinds.length > 1 && (
        <div role="tablist" className="mb-8 flex gap-8 border-b border-line">
          {kinds.map(k => (
            <button
              key={k}
              role="tab"
              aria-selected={kind === k}
              onClick={() => setKind(k)}
              className={`label -mb-px border-b-2 pb-3 ${kind === k ? 'border-red text-ink' : 'border-transparent hover:text-ink'}`}
            >
              {k === 'gp' ? 'Grand Prix' : 'Sprint'}
            </button>
          ))}
        </div>
      )}

      {!pred ? (
        <LockedButton gate={weekend.gates[kind]} label="Show predicted winner" finished={weekend.status === 'done'} />
      ) : phase === 'idle' ? (
        <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:gap-6">
          <ClickSpark sparkColor={['#e0362c', '#f4f4f5']} sparkCount={10} sparkRadius={26}>
            <button className="btn btn-red" onClick={() => setPhase(reduced ? 'shown' : 'loading')}>
              <Flag size={18} weight="fill" />
              Show predicted winner
            </button>
          </ClickSpark>
          <p className="text-sm">Uses {pred.sessions.practice} and {pred.sessions.qualifying} from this weekend.</p>
        </div>
      ) : (
        <AnimatePresence mode="wait">
          {phase === 'loading' ? (
            <motion.div key="load" exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.25 }}>
              <LoadingLog pred={pred} onDone={() => setPhase('shown')} />
            </motion.div>
          ) : (
            <motion.div key="shown" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <WinnerReveal pred={pred} drivers={weekend.drivers} />
              <FieldOdds pred={pred} drivers={weekend.drivers} />
              <ModelNote index={index} />
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </section>
  )
}
