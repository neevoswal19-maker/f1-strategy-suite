import { runMany, simulateRace, type SimConfig, type SimDriver } from './sim'

export interface SimRequest { id: number; drivers: SimDriver[]; cfg: SimConfig; n: number; seed: number }

// the featured race goes back first so its replay can start while the batch is still running
self.onmessage = (e: MessageEvent<SimRequest>) => {
  const { id, drivers, cfg, n, seed } = e.data
  self.postMessage({ id, featured: simulateRace(drivers, cfg, seed, true) })
  self.postMessage({ id, summary: runMany(drivers, cfg, n, seed + 1) })
}
