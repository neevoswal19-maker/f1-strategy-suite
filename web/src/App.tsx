import { useEffect } from 'react'
import { useHashWeekend, useIndex, useTrack, useWeekend } from './lib/data'
import Archive from './components/Archive'
import { Footer, Nav } from './components/Chrome'
import Hero from './components/Hero'
import LightsOut from './components/LightsOut'
import PredictPanel from './components/PredictPanel'
import SimPanel from './components/SimPanel'
import Timeline from './components/Timeline'
import Noise from './components/bits/Noise'

function Skeleton() {
  return (
    <div className="mx-auto max-w-[1400px] animate-pulse px-4 pt-16 sm:px-8" aria-busy="true" aria-label="Loading">
      <div className="h-4 w-48 bg-card" />
      <div className="mt-6 h-24 w-full max-w-[720px] bg-card" />
      <div className="mt-4 h-24 w-3/4 max-w-[560px] bg-card" />
      <div className="mt-12 grid grid-cols-3 gap-px">
        {[0, 1, 2].map(i => <div key={i} className="h-24 bg-card" />)}
      </div>
    </div>
  )
}

function Problem({ message }: { message: string }) {
  return (
    <div className="mx-auto max-w-[1400px] px-4 py-24 sm:px-8">
      <p className="label text-red">Red flag</p>
      <h1 className="mt-3 text-5xl">Couldn't load the data</h1>
      <p className="mt-4 max-w-[60ch]">{message}. Refresh in a minute; if it keeps happening the data job may be mid-update.</p>
    </div>
  )
}

export default function App() {
  const index = useIndex()
  const [hashId, go] = useHashWeekend()
  const id = hashId ?? index.data?.current ?? null
  // the current weekend refreshes every 5 minutes so a fresh prediction appears without a reload
  const weekend = useWeekend(id, id && id === index.data?.current ? 5 * 60_000 : 0)
  const track = useTrack(weekend.data?.track ?? null)

  useEffect(() => {
    if (weekend.data) document.title = `${weekend.data.name} · Pit Wall`
  }, [weekend.data])

  const viewingArchive = !!hashId && hashId !== index.data?.current
  return (
    <>
      <LightsOut />
      <Noise opacity={0.045} fps={12} fixed zIndex={60} />
      <Nav index={index.data} viewingArchive={viewingArchive} onCurrent={() => go(null)} />
      <main>
        {index.error || weekend.error ? (
          <Problem message={index.error ?? weekend.error ?? ''} />
        ) : !weekend.data ? (
          <Skeleton />
        ) : (
          <>
            <Hero weekend={weekend.data} track={track.data} />
            <Timeline weekend={weekend.data} />
            <PredictPanel weekend={weekend.data} index={index.data} />
            <SimPanel weekend={weekend.data} track={track.data} />
            {index.data && (
              <Archive
                index={index.data}
                activeId={weekend.data.id}
                onPick={wid => {
                  go(wid === index.data!.current ? null : wid)
                  window.scrollTo({ top: 0, behavior: 'smooth' })
                }}
              />
            )}
          </>
        )}
      </main>
      <Footer index={index.data} />
    </>
  )
}
