import { motion } from 'motion/react'
import { ArrowsClockwise, Crosshair, Gauge, XCircle } from '@phosphor-icons/react'
import type { Index } from '../lib/types'
import { pct } from '../lib/time'
import SectionHead from './SectionHead'

function Bar({ label, value, best }: { label: string; value: number; best?: boolean }) {
  return (
    <div className="grid grid-cols-[minmax(0,150px)_minmax(0,1fr)_48px] items-center gap-3 text-sm">
      <span className={best ? 'text-ink' : 'text-body'}>{label}</span>
      <div className="h-2 bg-soft" aria-hidden>
        <motion.div
          className={best ? 'h-full bg-red' : 'h-full bg-line-strong'}
          initial={{ width: 0 }}
          whileInView={{ width: `${value * 100}%` }}
          viewport={{ once: true }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
      <span className="num text-right text-ink">{pct(value, 0)}</span>
    </div>
  )
}

const recency = (hl: number | null) => (hl ? `recent races weighted, half-life ${hl}` : 'all races equal')

/** What the model re-learns after each race, how that compares, and where it went wrong. */
export default function LearningPanel({ index, onPick }: { index: Index; onPick: (id: string) => void }) {
  const m = index.model
  const L = m.learning
  if (!L) return null
  const learned = L.overall['Self-learning model']
  const fixed = L.overall['Original fixed model']
  const pole = L.overall['Pole sitter wins']
  const mistakes = index.mistakes ?? []

  return (
    <section id="learning" className="scroll-mt-16 border-t border-line bg-soft/40">
      <div className="mx-auto max-w-[1400px] px-4 py-20 sm:px-8 lg:py-28">
        <SectionHead title="How it learns">
          The forecast is a blend of {L.setups} versions of the model, from simple to complex, some favouring recent
          races. After every race, each version loses influence in proportion to how little chance it gave the real
          winner, so the ones that keep getting it wrong fade out. Every race since{' '}
          {L.firstRace ? Math.floor(L.firstRace / 100) : 2023} below was replayed this way, using only what the model
          knew at the time.
        </SectionHead>

        <div className="grid gap-px border border-line bg-line lg:grid-cols-3">
          <div className="bg-canvas p-5 sm:p-6">
            <p className="label flex items-center gap-2"><ArrowsClockwise size={14} weight="bold" />Trusted most right now</p>
            <ol className="mt-4 space-y-3">
              {L.trusted.map((t, i) => (
                <li key={i} className="grid grid-cols-[minmax(0,1fr)_48px] items-baseline gap-3">
                  <span className={i === 0 ? 'text-ink' : 'text-body'}>
                    {t.setup}
                    <span className="block text-xs text-muted">{recency(t.halfLife)}</span>
                  </span>
                  <span className="num text-right text-ink">{pct(t.weight, 0)}</span>
                </li>
              ))}
            </ol>
            <p className="mt-4 text-xs text-muted">
              Share of the forecast each version gets. Retrained on {m.trainingWeekends} weekends.
            </p>
          </div>

          <div className="bg-canvas p-5 sm:p-6">
            <p className="label flex items-center gap-2"><Crosshair size={14} weight="bold" />{L.replayed} races replayed since {L.firstRace ? Math.floor(L.firstRace / 100) : 2023}</p>
            <p className="mt-2 text-xs text-muted">Top pick won the race</p>
            <div className="mt-4 space-y-3">
              {learned && <Bar label="Self-learning model" value={learned.topPickWon} best />}
              {fixed && <Bar label="Original fixed model" value={fixed.topPickWon} />}
              {pole && <Bar label="Pole sitter wins" value={pole.topPickWon} />}
            </div>
            {L.eras && (
              <ul className="mt-5 space-y-1 border-t border-line pt-4 text-xs">
                {Object.entries(L.eras).map(([era, e]) => (
                  <li key={era} className="flex justify-between gap-3">
                    <span>{era}, {e.races} races</span>
                    <span className="num text-ink">
                      {pct(e['Self-learning model']?.topPickWon ?? 0, 0)}
                      <span className="text-muted"> vs pole {pct(e['Pole sitter wins']?.topPickWon ?? 0, 0)}</span>
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {learned?.logLoss != null && fixed?.logLoss != null && (
              <p className="mt-5 text-sm">
                Its percentages are more reliable too: prediction error (log-loss){' '}
                <span className="num text-ink">{learned.logLoss.toFixed(2)}</span> against{' '}
                <span className="num">{fixed.logLoss.toFixed(2)}</span> before. Lower is better.
              </p>
            )}
          </div>

          <div className="bg-canvas p-5 sm:p-6">
            <p className="label flex items-center gap-2"><Gauge size={14} weight="bold" />Does it mean what it says?</p>
            <ul className="mt-5 divide-y divide-line border-y border-line text-sm">
              {L.calibration.map((c, i) => (
                <li key={i} className="flex items-baseline justify-between gap-3 py-2.5">
                  <span>Said <span className="num text-ink">{pct(c.said, 0)}</span></span>
                  <span>won <span className="num text-ink">{pct(c.won, 0)}</span></span>
                  <span className="num text-xs text-muted">{c.races} races</span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-muted">The top pick's win chance against how often that driver actually won.</p>
          </div>
        </div>

        <div className="mt-14 grid gap-10 lg:grid-cols-2">
          <div>
            <h3 className="text-3xl">Learning log</h3>
            <ol className="mt-4 divide-y divide-line border-y border-line text-sm">
              {L.history.map(h => (
                <li key={h.raceId} className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1 py-3">
                  <span className="text-ink">{h.race.replace(' Grand Prix', '')}</span>
                  <span className={`num text-right ${h.hit ? 'text-go' : 'text-red'}`}>
                    {h.picked} {pct(h.pickWin, 0)} {h.hit ? 'won' : `· ${h.winner} won`}
                  </span>
                  <span className="col-span-2 text-xs text-muted">
                    Most trusted going in: {h.setup}, {recency(h.halfLife)} ({pct(h.trust, 0)})
                  </span>
                </li>
              ))}
            </ol>
          </div>
          <div>
            <h3 className="text-3xl">Recent mistakes</h3>
            {mistakes.length === 0 ? (
              <p className="mt-4 text-sm">No misses yet.</p>
            ) : (
              <ol className="mt-4 divide-y divide-line border-y border-line text-sm">
                {mistakes.map(x => (
                  <li key={x.id}>
                    <button onClick={() => onPick(x.id)} className="flex w-full gap-3 py-3 text-left hover:bg-card">
                      <XCircle size={18} weight="fill" className="mt-0.5 shrink-0 text-red/80" />
                      <span>
                        <span className="text-ink">{x.name.replace(' Grand Prix', '')} {x.id.slice(0, 4)}:</span>{' '}
                        picked {x.predicted} ({pct(x.predictedWin, 0)}), {x.actual} won
                        {x.actualGrid ? ` from P${x.actualGrid}` : ''}
                        {x.actualWin != null ? `. It gave ${x.actual} ${pct(x.actualWin, 0)}.` : '.'}
                      </span>
                    </button>
                  </li>
                ))}
              </ol>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
