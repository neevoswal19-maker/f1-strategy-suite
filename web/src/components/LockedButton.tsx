import { useId } from 'react'
import { LockSimple, Hourglass } from '@phosphor-icons/react'
import type { Gate } from '../lib/types'
import { countdown, fmtWhen, useNow } from '../lib/time'

/** The disabled state of a gated button, with why it is locked and when it opens. */
export default function LockedButton({ gate, label, finished = false }: { gate?: Gate; label: string; finished?: boolean }) {
  const now = useNow(1000)
  const why = useId()
  const unlockAt = gate?.unlockAt ? new Date(gate.unlockAt).getTime() : null
  const waiting = unlockAt !== null && now >= unlockAt
  return (
    <div className="flex flex-col items-start gap-3">
      <button className="btn btn-locked w-full sm:w-auto" disabled aria-describedby={why}>
        {waiting ? <Hourglass size={18} weight="bold" /> : <LockSimple size={18} weight="bold" />}
        {label}
      </button>
      <p id={why} className="text-sm text-body">
        {gate?.reason === 'not-enough-history' ? (
          'No prediction for this race: the model needs at least 8 earlier weekends to learn from, and its history starts in 2019.'
        ) : finished ? (
          'No prediction for this race: OpenF1 has no usable practice or qualifying laps for it.'
        ) : !gate || !unlockAt ? (
          'Unlocks once this weekend\'s qualifying is over.'
        ) : waiting ? (
          <>{gate.session} is over. This unlocks once the next data update has read the laps, usually within the hour.</>
        ) : (
          <>
            Unlocks after {gate.session}, {fmtWhen(gate.unlockAt!)}
            <span className="num ml-2 text-ink">({countdown(unlockAt - now)})</span>
          </>
        )}
      </p>
    </div>
  )
}
