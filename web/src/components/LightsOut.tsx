import { useEffect, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { usePrefersReducedMotion } from '../lib/time'

const KEY = 'pitwall-intro-seen'

function seen() {
  try {
    return sessionStorage.getItem(KEY) === '1'
  } catch {
    return false
  }
}

/** Five red lights come on one by one, hold, then go out. Plays once per browser session. */
export default function LightsOut() {
  const reduced = usePrefersReducedMotion()
  const [lit, setLit] = useState(0)
  const [show, setShow] = useState(() => !seen())
  const [out, setOut] = useState(false)

  useEffect(() => {
    if (!show) return
    if (reduced) {
      setShow(false)
      return
    }
    const timers: number[] = []
    for (let i = 1; i <= 5; i++) timers.push(window.setTimeout(() => setLit(i), 350 + i * 420))
    // the hold before lights out is random in real starts
    const hold = 350 + 5 * 420 + 500 + Math.random() * 700
    timers.push(window.setTimeout(() => {
      setLit(0)
      setOut(true)
    }, hold))
    timers.push(window.setTimeout(() => {
      setShow(false)
      try {
        sessionStorage.setItem(KEY, '1')
      } catch {
        /* private mode: the intro just plays again */
      }
    }, hold + 450))
    return () => timers.forEach(clearTimeout)
  }, [show, reduced])

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          className="fixed inset-0 z-50 grid place-items-center bg-canvas"
          exit={{ opacity: 0, scale: 1.04 }}
          transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
          onClick={() => setShow(false)}
          role="presentation"
        >
          <div className="flex flex-col items-center gap-10 px-4">
            <div className="flex gap-3 sm:gap-5" aria-hidden>
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className="flex flex-col gap-2 border border-line bg-soft p-2 sm:gap-3 sm:p-3">
                  {[0, 1].map(row => (
                    <div
                      key={row}
                      className="size-9 rounded-full transition-[background-color,box-shadow] duration-100 sm:size-14"
                      style={{
                        background: lit >= i ? '#ff2a1f' : '#26262c',
                        boxShadow: lit >= i ? '0 0 28px 6px rgba(255,42,31,.55)' : 'none',
                      }}
                    />
                  ))}
                </div>
              ))}
            </div>
            <p className="label text-muted">{out ? 'Lights out' : lit === 5 ? 'Hold' : 'Formation lap complete'}</p>
            <button className="label text-muted underline-offset-4 hover:text-ink hover:underline" onClick={() => setShow(false)}>
              Skip
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
