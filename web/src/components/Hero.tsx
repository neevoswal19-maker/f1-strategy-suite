import { motion } from 'motion/react'
import type { Track, Weekend } from '../lib/types'
import { countdown, fmtDate, fmtWhen, useNow } from '../lib/time'
import TrackMap from './TrackMap'

function SplitHeading({ text }: { text: string }) {
  const words = text.toUpperCase().split(' ')
  return (
    <h1 className="text-[clamp(3rem,8.5vw,6rem)] leading-[0.88] tracking-[-0.01em]" aria-label={text}>
      {words.map((w, wi) => (
        <span key={wi} className="mr-[0.22em] inline-block overflow-hidden pb-[0.04em] align-bottom" aria-hidden>
          <motion.span
            className="inline-block"
            initial={{ y: '105%' }}
            animate={{ y: 0 }}
            transition={{ type: 'spring', stiffness: 110, damping: 20, delay: 0.15 + wi * 0.09 }}
          >
            {w}
          </motion.span>
        </span>
      ))}
    </h1>
  )
}

function SpeedLines() {
  // decorative streaks drifting across the hero, CSS-only
  const lines = [12, 27, 41, 58, 66, 79, 88]
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
      {lines.map((top, i) => (
        <span
          key={i}
          className="speedline absolute left-0 h-px"
          style={{
            top: `${top}%`,
            width: `${14 + (i % 3) * 9}vw`,
            background: 'linear-gradient(90deg, transparent, rgba(244,244,245,.16), transparent)',
            animationDuration: `${2.6 + (i % 4) * 0.9}s`,
            animationDelay: `${i * 0.37}s`,
          }}
        />
      ))}
    </div>
  )
}

export default function Hero({ weekend, track }: { weekend: Weekend; track: Track | null }) {
  const now = useNow(1000)
  const next = weekend.sessions.find(s => new Date(s.start).getTime() > now)
  const race = new Date(weekend.raceStart).getTime()
  const live = weekend.sessions.find(s => {
    const t = new Date(s.start).getTime()
    return t <= now && now < t + (s.name === 'Race' ? 2 : 1) * 3600_000
  })

  return (
    <section className="relative overflow-hidden border-b border-line">
      <SpeedLines />
      <div className="mx-auto grid max-w-[1400px] gap-10 px-4 pb-14 pt-10 sm:px-8 lg:grid-cols-[1.15fr_1fr] lg:gap-6 lg:pb-20 lg:pt-16">
        <div className="relative flex flex-col justify-between gap-10">
          <div>
            <SplitHeading text={weekend.name} />
            <motion.p
              className="label mt-6 flex flex-wrap items-center gap-x-3 gap-y-1"
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1], delay: 0.4 }}
            >
              <span className="text-red">Round {weekend.round}</span>
              <span className="h-3 w-px bg-line-strong" />
              <span>{weekend.locality}, {weekend.country}</span>
              {weekend.sprint && (
                <>
                  <span className="h-3 w-px bg-line-strong" />
                  <span className="text-ink">Sprint weekend</span>
                </>
              )}
            </motion.p>
            <p className="mt-3 max-w-[52ch] text-body">
              {weekend.circuitName} · {weekend.circuit.laps} laps · race {fmtWhen(weekend.raceStart)} your time
            </p>
          </div>

          <div className="grid grid-cols-2 gap-px border border-line bg-line sm:grid-cols-3">
            <div className="bg-canvas p-4 sm:p-5">
              <p className="label">{live ? 'On track now' : next ? `${next.name} in` : 'Race'}</p>
              <p className="num mt-2 text-2xl font-medium text-ink sm:text-3xl">
                {live ? (
                  <span className="flex items-center gap-2">
                    <span className="live-dot size-2.5 rounded-full bg-red" /> {live.name}
                  </span>
                ) : next ? (
                  countdown(new Date(next.start).getTime() - now)
                ) : (
                  'Finished'
                )}
              </p>
            </div>
            <div className="bg-canvas p-4 sm:p-5">
              <p className="label">Lights out</p>
              <p className="num mt-2 text-2xl font-medium text-ink sm:text-3xl">
                {race > now ? countdown(race - now) : fmtDate(weekend.raceStart)}
              </p>
            </div>
            <div className="col-span-2 bg-canvas p-4 sm:col-span-1 sm:p-5">
              <p className="label">Rain chance</p>
              <p className="num mt-2 text-2xl font-medium text-ink sm:text-3xl">
                {weekend.forecast ? `${Math.round(weekend.forecast.rainChance * 100)}%` : '—'}
                <span className="ml-2 font-sans text-xs font-normal text-muted">
                  {weekend.forecast?.source === 'forecast' ? 'Open-Meteo' : weekend.forecast ? 'no forecast yet' : 'past race'}
                </span>
              </p>
            </div>
          </div>
        </div>

        <motion.div
          className="relative min-h-[320px] lg:min-h-[480px]"
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
        >
          <TrackMap track={track} ambient className="absolute inset-x-0 top-0 bottom-14 h-[calc(100%-3.5rem)] w-full" />
          <div className="absolute bottom-0 right-0 flex gap-6 text-right">
            <div>
              <p className="label">Overtaking</p>
              <p className="num text-ink">{weekend.circuit.overtaking > 0.7 ? 'Hard' : weekend.circuit.overtaking > 0.45 ? 'Medium' : 'Easy'}</p>
            </div>
            <div>
              <p className="label">Safety car</p>
              <p className="num text-ink">{Math.round(weekend.circuit.scChance * 100)}%</p>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
