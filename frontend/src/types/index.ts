export type LearnerLevel = 'beginner' | 'starter' | 'experienced'
export type LearningGoal = 'understand' | 'project' | 'interview'

export interface LearningSpaceInput {
  topic: string
  level: LearnerLevel
  goal: LearningGoal
  dailyMinutes: 15 | 30 | 60 | 90
}

export interface LearningSpace {
  id: string
  topic: string
  status: 'created' | 'analyzing' | 'ready' | 'failed'
}

export interface Source {
  source_key: string
  title: string
  author_name: string
  source_url: string
  excerpt: string
}

export interface Consensus {
  id: string
  title: string
  detail: string
  source_keys: string[]
}

export interface DisagreementSide {
  title: string
  reason: string
  suitable_for: string[]
  source_keys: string[]
}

export interface Disagreement {
  id: string
  question: string
  side_a: DisagreementSide
  side_b: DisagreementSide
  how_to_choose: string
}

export interface Analysis {
  overview: string
  consensus: Consensus[]
  disagreements: Disagreement[]
  concepts: { id: string; label: string; description: string; category: string }[]
  edges: { source: string; target: string; type: string; label?: string }[]
  warnings: string[]
}
