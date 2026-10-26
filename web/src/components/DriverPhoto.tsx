import { useState } from 'react'
import type { DriverCard } from '../lib/types'

interface Props {
  driver?: DriverCard
  code: string
  size?: number
  className?: string
  /** no colour tile behind the photo */
  plain?: boolean
}

/** Official headshot (via OpenF1) on a team-colour tile, with initials if the image fails. */
export default function DriverPhoto({ driver, code, size = 48, className = '', plain = false }: Props) {
  const [failed, setFailed] = useState(false)
  const colour = driver?.colour ?? '#3a3a43'
  const name = driver ? `${driver.first} ${driver.last}` : code
  return (
    <div
      className={`relative shrink-0 overflow-hidden ${className}`}
      style={{
        width: size,
        height: size,
        background: plain ? 'transparent' : `linear-gradient(160deg, ${colour} 0%, ${colour}55 55%, #17171b 100%)`,
      }}
    >
      {driver?.photo && !failed ? (
        <img
          src={driver.photo.replace('/1col/', size > 120 ? '/4col/' : '/2col/')}
          alt={name}
          loading="lazy"
          decoding="async"
          onError={() => setFailed(true)}
          className="absolute inset-0 h-full w-full object-cover object-top"
        />
      ) : (
        <span
          aria-label={name}
          className="absolute inset-0 grid place-items-center font-display font-bold text-white/90"
          style={{ fontSize: size * 0.36 }}
        >
          {code}
        </span>
      )}
    </div>
  )
}
