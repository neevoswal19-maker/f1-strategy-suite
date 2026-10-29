// Shapes of the JSON written by pipeline/build.py

export type ParamKey =
  | 'grid' | 'quali_pace' | 'race_pace' | 'car' | 'driver'
  | 'track_confidence' | 'track_form' | 'reliability' | 'racecraft' | 'wet_skill'

export interface SimParam { key: ParamKey; label: string; desc: string }

export interface SimulatorCard {
  weights: Record<ParamKey, number>
  params: SimParam[]
  fittedOn: number
}

export interface Reason { key: string; title: string; impact: number; text: string }

export interface DriverResult {
  code: string
  win: number
  podium: number
  expPos: number
  qPos: number
  team: string
  reasons: Reason[]
  ratings: Record<ParamKey, number>
  raw: Record<ParamKey, string>
}

export interface Prediction {
  kind: 'gp' | 'sprint'
  label: string
  rainChance: number
  rainSource: 'forecast' | 'default'
  sessions: { practice: string | null; qualifying: string }
  counts: { drivers: number; trainingWeekends: number }
  results: DriverResult[]
  predictedWinner: string
  actualWinner: string | null
  hit: boolean | null
}

export interface Gate {
  session: string
  sessionStart: string | null
  unlockAt: string | null
  unlocked: boolean
  reason: 'locked' | 'ready' | 'waiting-for-data' | 'not-enough-history'
}

export interface DriverCard {
  code: string
  number: number
  first: string
  last: string
  team: string
  colour: string
  photo: string | null
}

export interface CircuitStats {
  overtaking: number
  scChance: number
  neutralisedChance: number
  laps: number
  pastRaces: number
  pitLoss?: number
}

export interface Weekend {
  id: string
  season: number
  round: number
  name: string
  circuitId: string
  circuitName: string
  locality: string
  country: string
  raceStart: string
  sprint: boolean
  status: 'done' | 'current' | 'upcoming'
  sessions: { name: string; start: string }[]
  gates: Partial<Record<'gp' | 'sprint', Gate>>
  track: string | null
  circuit: CircuitStats
  forecast: { rainChance: number; source: string } | null
  drivers: Record<string, DriverCard>
  prediction: Partial<Record<'gp' | 'sprint', Prediction>>
  simulator: SimulatorCard
  model: { name: string; window: { races: number; from: number; to: number } }
  generatedAt: string
}

export interface WeekendSummary {
  id: string
  round: number
  name: string
  locality: string
  country: string
  circuitId: string
  raceStart: string
  sprint: boolean
  status: Weekend['status']
  track: string | null
  predicted: string | null
  predictedWin: number | null
  actual: string | null
  hit: boolean | null
  unlocked: boolean
  actualWin?: number | null
  actualGrid?: number | null
}

export interface LearningEntry {
  raceId: number
  race: string
  setup: string
  halfLife: number | null
  trust: number
  picked: string
  pickWin: number
  winner: string
  winnerP: number | null
  hit: boolean
  fixedHit: boolean
  poleHit: boolean
}

export interface Mistake {
  id: string
  name: string
  predicted: string
  predictedWin: number
  actual: string
  actualWin: number | null
  actualGrid: number | null
}

export interface BacktestRow { topPickWon: number; winnerInTop3: number; avgPWinner?: number; logLoss?: number }

export interface SeasonSummary {
  season: number
  hitRate: { hits: number; races: number }
  weekends: WeekendSummary[]
}

export interface Index {
  season: number
  generatedAt: string
  current: string
  hitRate: { hits: number; races: number }
  seasons?: { season: number; hits: number; races: number }[]
  model: {
    name: string
    backtest: Record<string, BacktestRow>
    window: { races: number; from: number; to: number }
    importance: Record<string, number>
    trainingWeekends: number
    features: string[]
    learning?: {
      trusted: { setup: string; halfLife: number | null; weight: number }[]
      calibration: { said: number; won: number; races: number }[]
      setups: number
      replayed: number
      overall: Record<string, BacktestRow>
      recent: Record<string, BacktestRow>
      eta: number
      alpha: number
      eras?: Record<string, Record<string, BacktestRow> & { races: number }>
      firstRace?: number
      history: LearningEntry[]
    }
  }
  mistakes?: Mistake[]
  simulator: SimulatorCard
  weekends: WeekendSummary[]
}

export interface Track {
  circuitId: string
  name: string
  viewBox: [number, number, number, number]
  points: [number, number][]
  corners: { n: number; x: number; y: number }[]
  pitLoss: number | null
}
