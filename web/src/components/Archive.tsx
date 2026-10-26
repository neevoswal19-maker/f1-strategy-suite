import { motion } from 'motion/react'
import { CheckCircle, XCircle, LockSimple } from '@phosphor-icons/react'
import type { Index } from '../lib/types'
import { fmtDate, pct } from '../lib/time'
import SectionHead from './SectionHead'

export default function Archive({ index, activeId, onPick }: { index: Index; activeId: string; onPick: (id: string) => void }) {
  const { hits, races } = index.hitRate
  return (
    <section id="season" className="scroll-mt-16 border-t border-line">
      <div className="mx-auto max-w-[1400px] px-4 py-20 sm:px-8 lg:py-28">
        <SectionHead title={`${index.season} season`}>
          Every finished round, predicted the same way: with only the data that existed after qualifying, and a
          model trained on earlier weekends.{' '}
          {races > 0 && (
            <span className="text-ink">
              It picked the winner in <span className="num">{hits}</span> of <span className="num">{races}</span> races ({pct(hits / races, 0)}).
            </span>
          )}
        </SectionHead>
        <ol className="grid grid-cols-1 gap-px border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
          {index.weekends.map((w, i) => {
            const active = w.id === activeId
            const clickable = w.status !== 'upcoming' || w.unlocked
            return (
              <motion.li
                key={w.id}
                initial={{ opacity: 0 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true, margin: '-40px' }}
                transition={{ delay: (i % 4) * 0.05 }}
                className="bg-canvas"
              >
                <button
                  onClick={() => clickable && onPick(w.id)}
                  disabled={!clickable}
                  aria-current={active ? 'page' : undefined}
                  className={`group relative flex h-full w-full flex-col justify-between gap-6 p-5 text-left transition-colors ${
                    active ? 'bg-card' : clickable ? 'hover:bg-card' : 'opacity-50'
                  }`}
                >
                  {active && <span className="absolute inset-x-0 top-0 h-[3px] bg-red" />}
                  <div>
                    <p className="font-display text-2xl font-bold uppercase leading-none text-ink">
                      {w.name.replace(' Grand Prix', '')}
                    </p>
                    <p className="num mt-2 flex items-center justify-between gap-2 text-xs text-muted">
                      <span>R{String(w.round).padStart(2, '0')} · {fmtDate(w.raceStart)} · {w.locality}</span>
                      {w.status === 'current' ? <span className="font-sans text-red">This weekend</span> : w.sprint ? <span className="font-sans">Sprint</span> : null}
                    </p>
                  </div>
                  <div className="flex items-end justify-between gap-3 text-sm">
                    {w.predicted ? (
                      <div>
                        <p className="text-xs text-muted">Predicted</p>
                        <p className="num text-ink">{w.predicted} <span className="text-muted">{w.predictedWin ? pct(w.predictedWin, 0) : ''}</span></p>
                      </div>
                    ) : (
                      <p className="flex items-center gap-1.5 text-xs text-muted"><LockSimple size={13} weight="bold" />{w.status === 'done' ? 'No weekend data' : 'After qualifying'}</p>
                    )}
                    {w.actual && (
                      <div className="flex items-center gap-2 text-right">
                        <div>
                          <p className="text-xs text-muted">Winner</p>
                          <p className="num text-ink">{w.actual}</p>
                        </div>
                        {w.hit === true && <CheckCircle size={22} weight="fill" className="text-go" aria-label="correct" />}
                        {w.hit === false && <XCircle size={22} weight="fill" className="text-red/80" aria-label="missed" />}
                      </div>
                    )}
                  </div>
                </button>
              </motion.li>
            )
          })}
        </ol>
      </div>
    </section>
  )
}
