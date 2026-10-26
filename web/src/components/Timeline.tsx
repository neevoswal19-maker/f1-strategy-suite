import type React from 'react'
import { motion } from 'motion/react'
import { Check, LockSimple, LockSimpleOpen } from '@phosphor-icons/react'
import type { Weekend } from '../lib/types'
import { fmtDay, fmtTime, SESSION_SHORT, useNow } from '../lib/time'

const UNLOCKS: Record<string, string> = { Qualifying: 'Unlocks GP prediction', 'Sprint Qualifying': 'Unlocks sprint prediction' }

export default function Timeline({ weekend }: { weekend: Weekend }) {
  const now = useNow(30_000)
  return (
    <section aria-label="Weekend schedule" className="border-b border-line">
      <ol
        className="mx-auto grid max-w-[1400px] grid-cols-2 sm:grid-cols-3 lg:[grid-template-columns:repeat(var(--n),minmax(0,1fr))]"
        style={{ '--n': weekend.sessions.length } as React.CSSProperties}
      >
        {weekend.sessions.map((s, i) => {
          const start = new Date(s.start).getTime()
          const len = s.name === 'Race' ? 2 : 1
          const done = now > start + len * 3600_000
          const live = now >= start && !done
          const unlock = UNLOCKS[s.name]
          return (
            <motion.li
              key={s.name}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className={`relative border-line px-4 py-5 sm:px-6 [&:not(:last-child)]:border-r ${
                unlock ? 'bg-soft' : ''
              } border-b lg:border-b-0`}
            >
              {live && <span className="absolute inset-x-0 top-0 h-[3px] bg-red" />}
              <div className="flex items-center justify-between gap-2">
                <span className={`font-display text-2xl font-bold ${done ? 'text-muted' : 'text-ink'}`}>
                  {SESSION_SHORT[s.name] ?? s.name}
                </span>
                {done ? (
                  <Check size={16} weight="bold" className="text-go" aria-label="finished" />
                ) : live ? (
                  <span className="label flex items-center gap-1.5 text-red"><span className="live-dot size-2 rounded-full bg-red" />Live</span>
                ) : null}
              </div>
              <p className="num mt-1 text-sm text-body">{fmtDay(s.start)} · {fmtTime(s.start)}</p>
              {unlock && (
                <p className={`mt-2 flex items-center gap-1.5 text-xs ${done ? 'text-go' : 'text-muted'}`}>
                  {done ? <LockSimpleOpen size={13} weight="bold" /> : <LockSimple size={13} weight="bold" />}
                  {unlock}
                </p>
              )}
            </motion.li>
          )
        })}
      </ol>
    </section>
  )
}
