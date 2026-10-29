import { ArrowLeft, GithubLogo, Notebook } from '@phosphor-icons/react'
import type { Index } from '../lib/types'

const REPO = 'https://github.com/neevoswal19-maker/f1-strategy-suite'
const COLAB = 'https://colab.research.google.com/github/neevoswal19-maker/f1-strategy-suite/blob/main/notebook/F1_Strategy_Intelligence_Suite.ipynb'

// section links scroll without touching the URL hash, which holds the selected weekend
const jump = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })

export function Nav({ viewingArchive, onCurrent }: { viewingArchive: boolean; onCurrent: () => void }) {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-canvas/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between gap-4 px-4 sm:px-8">
        <a href="#" onClick={e => { e.preventDefault(); onCurrent() }} className="flex items-center gap-3" aria-label="Pit Wall home">
          <span className="flex gap-1" aria-hidden>
            {[0, 1, 2].map(i => <span key={i} className="size-2.5 rounded-full bg-red" />)}
          </span>
          <span className="font-display text-2xl font-bold uppercase tracking-wide text-ink">Pit Wall</span>
        </a>
        <nav className="flex items-center gap-1 sm:gap-6">
          {viewingArchive && (
            <button onClick={onCurrent} className="label flex min-h-11 items-center gap-1.5 px-2 text-ink hover:text-red">
              <ArrowLeft size={14} weight="bold" /> This weekend
            </button>
          )}
          <button onClick={() => jump('prediction')} className="label hidden min-h-11 items-center hover:text-ink md:flex">Prediction</button>
          <button onClick={() => jump('simulator')} className="label hidden min-h-11 items-center hover:text-ink md:flex">Simulator</button>
          <button onClick={() => jump('season')} className="label hidden min-h-11 items-center hover:text-ink md:flex">Seasons</button>
          <a href={COLAB} target="_blank" rel="noreferrer" className="grid size-11 place-items-center rounded-full bg-card text-ink hover:bg-raised" aria-label="Open the strategy notebook in Colab">
            <Notebook size={18} />
          </a>
        </nav>
      </div>
    </header>
  )
}

export function Footer({ index }: { index: Index | null }) {
  return (
    <footer className="border-t border-line">
      <div className="kerb opacity-80" />
      <div className="mx-auto grid max-w-[1400px] gap-10 px-4 py-14 text-sm sm:px-8 md:grid-cols-[2fr_1fr_1fr]">
        <div>
          <p className="font-display text-3xl font-bold uppercase text-ink">Pit Wall</p>
          <p className="mt-3 max-w-[52ch]">
            Part of the F1 Strategy Intelligence Suite. The tyre strategy and pit-wall simulator lives in the Colab
            notebook; this site handles race winners.
          </p>
          <div className="mt-5 flex flex-wrap gap-3">
            <a className="btn btn-ghost min-h-11 px-4 text-xs" href={COLAB} target="_blank" rel="noreferrer"><Notebook size={16} /> Strategy notebook</a>
            <a className="btn btn-ghost min-h-11 px-4 text-xs" href={REPO} target="_blank" rel="noreferrer"><GithubLogo size={16} /> Source</a>
          </div>
        </div>
        <div>
          <p className="label mb-3">Data</p>
          <ul className="space-y-1.5">
            <li><a className="hover:text-ink" href="https://openf1.org" target="_blank" rel="noreferrer">OpenF1</a>: practice, qualifying, drivers</li>
            <li><a className="hover:text-ink" href="https://github.com/jolpica/jolpica-f1" target="_blank" rel="noreferrer">Jolpica (Ergast)</a>: results</li>
            <li><a className="hover:text-ink" href="https://open-meteo.com" target="_blank" rel="noreferrer">Open-Meteo</a>: rain forecast</li>
            <li>MultiViewer: track layouts</li>
          </ul>
        </div>
        <div>
          <p className="label mb-3">Updated</p>
          <p className="num text-ink">{index ? new Date(index.generatedAt).toLocaleString() : '—'}</p>
          <p className="mt-2 text-xs text-muted">Refreshes every 20 minutes on race weekends.</p>
        </div>
      </div>
      <p className="mx-auto max-w-[1400px] px-4 pb-10 text-xs text-muted sm:px-8">
        Unofficial fan project, not associated with Formula 1 or the FIA. F1 and Formula 1 are trademarks of Formula One Licensing B.V.
        Driver photos are loaded from formula1.com through OpenF1.
      </p>
    </footer>
  )
}
