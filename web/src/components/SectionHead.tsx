import type { ReactNode } from 'react'

export default function SectionHead({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <header className="mb-10 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:items-end">
      <h2 className="text-[clamp(2.4rem,5.5vw,4.5rem)] [text-wrap:balance]">
        <span className="mb-4 block h-[3px] w-12 bg-red" aria-hidden />
        {title}
      </h2>
      {children && <div className="max-w-[58ch] text-body lg:justify-self-end">{children}</div>}
    </header>
  )
}
