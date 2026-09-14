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
  level?: LearnerLevel
  goal?: LearningGoal
  daily_minutes?: number
  status: 'created' | 'analyzing' | 'ready' | 'failed'
  error_message?: string | null
}

export interface Source {
  source_key: string
  title: string
  author_name: string
  source_url: string
  excerpt: string
  provider?: 'zhihu' | 'demo'
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

export interface StudyDay {
  day: number
  title: string
  goal: string
  activities: string[]
  output: string
  self_check: string
  estimated_minutes: number
}

export interface StudyPlan {
  strategy: string
  days: StudyDay[]
}

export interface Quiz {
  id: string
  learning_space_id: string
  concept_id?: string | null
  question: string
  source_keys: string[]
}

export interface Grade {
  id: string
  quiz_id: string
  score: number
  strengths: string[]
  improvements: string[]
  next_step: string
}

export interface CompleteLearningSpace {
  space: LearningSpace
  sources: Source[]
  analysis?: Analysis
  plan?: StudyPlan
  quizzes?: Quiz[]
}
