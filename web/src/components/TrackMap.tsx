import { forwardRef, memo, useEffect, useImperativeHandle, useMemo, useRef } from 'react'
import { motion } from 'motion/react'
import type { Track } from '../lib/types'
import { usePrefersReducedMotion } from '../lib/time'

export interface TrackMapHandle {
  /** Place car dots: progress 0-1 around the lap, per car code. */
  place: (progress: Record<string, number>) => void
}

interface Props {
  track: Track | null
  cars?: { code: string; colour: string }[]
  /** a single glowing car lapping on its own (hero mode) */
  ambient?: boolean
  className?: string
}

const AMBIENT_LAP_MS = 9000

const TrackMap = forwardRef<TrackMapHandle, Props>(function TrackMap({ track, cars = [], ambient, className = '' }, ref) {
  const pathRef = useRef<SVGPathElement>(null)
  const dotRefs = useRef<Record<string, SVGGElement | null>>({})
  const ghostRef = useRef<SVGCircleElement>(null)
  const reduced = usePrefersReducedMotion()

  const d = useMemo(() => {
    if (!track) return ''
    return track.points.map(([x, y], i) => `${i ? 'L' : 'M'}${x} ${y}`).join(' ') + ' Z'
  }, [track])

  useImperativeHandle(ref, () => ({
    place(progress) {
      const path = pathRef.current
      if (!path) return
      const len = path.getTotalLength()
      for (const [code, p] of Object.entries(progress)) {
        const g = dotRefs.current[code]
        if (!g) continue
        if (!Number.isFinite(p)) {
          g.style.opacity = '0'
          continue
        }
        const pt = path.getPointAtLength((((p % 1) + 1) % 1) * len)
        g.style.opacity = '1'
        g.setAttribute('transform', `translate(${pt.x} ${pt.y})`)
      }
    },
  }))

  // the ambient car in the hero: one car lapping forever
  useEffect(() => {
    if (!ambient || reduced || !track) return
    let raf = 0
    const start = performance.now()
    const tick = (now: number) => {
      const path = pathRef.current
      const ghost = ghostRef.current
      if (path && ghost) {
        const p = ((now - start) % AMBIENT_LAP_MS) / AMBIENT_LAP_MS
        const pt = path.getPointAtLength(p * path.getTotalLength())
        ghost.setAttribute('cx', String(pt.x))
        ghost.setAttribute('cy', String(pt.y))
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [ambient, reduced, track])

  if (!track) {
    return (
      <div className={`grid place-items-center border border-line text-muted ${className}`}>
        <span className="label">Track map not available yet</span>
      </div>
    )
  }
  const [, , w, h] = track.viewBox
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className={className} role="img" aria-label={`${track.name ?? 'Circuit'} layout`}>
      <defs>
        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="6" result="b" />
          <feMerge>
            <feMergeNode in="b" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <path d={d} fill="none" stroke="#1f1f25" strokeWidth={26} strokeLinejoin="round" />
      <motion.path
        ref={pathRef}
        d={d}
        fill="none"
        stroke="#f4f4f5"
        strokeWidth={5}
        strokeLinejoin="round"
        initial={reduced ? false : { pathLength: 0, opacity: 0.4 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 2.2, ease: [0.16, 1, 0.3, 1] }}
      />
      {/* start / finish line */}
      {track.points.length > 1 && (
        <g transform={`translate(${track.points[0][0]} ${track.points[0][1]})`}>
          <rect x={-9} y={-9} width={18} height={18} className="fill-red" />
        </g>
      )}
      {track.corners.map(c => (
        <text key={c.n} x={c.x} y={c.y} className="fill-muted num" fontSize={20} textAnchor="middle" dy={7} opacity={0.55}>
          {c.n}
        </text>
      ))}
      {ambient && !reduced && (
        <circle ref={ghostRef} r={11} className="fill-red" filter="url(#glow)" cx={track.points[0][0]} cy={track.points[0][1]} />
      )}
      {cars.map(c => (
        <g key={c.code} ref={el => { dotRefs.current[c.code] = el }} style={{ opacity: 0 }}>
          <circle r={13} fill={c.colour} stroke="#0c0c0e" strokeWidth={3} />
          <text y={-20} textAnchor="middle" fontSize={17} className="fill-ink num" fontWeight={600}>{c.code}</text>
        </g>
      ))}
    </svg>
  )
})

export default memo(TrackMap)
