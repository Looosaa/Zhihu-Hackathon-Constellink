import type { ReactNode } from 'react'

export function ConsensusCard({ children }: { children?: ReactNode }) { return <section>{children ?? '共识观点将在 AI 分析后展示'}</section> }
