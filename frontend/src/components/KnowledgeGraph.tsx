import { useMemo, useState } from 'react'
import { ArrowUpRight, CircleHelp, GitBranch, LayoutGrid, Route } from 'lucide-react'

type GraphNode = {
  id: string
  label: string
  description: string
  category: string
}

type GraphEdge = {
  source: string
  target: string
  type: string
  label?: string
}

type KnowledgeGraphProps = {
  nodes: GraphNode[]
  edges: GraphEdge[]
  isLive: boolean
  onOpen: () => void
}

const constellationPositions = [
  { x: 4, y: 37 },
  { x: 28, y: 8 },
  { x: 28, y: 66 },
  { x: 52, y: 8 },
  { x: 52, y: 66 },
  { x: 76, y: 37 },
  { x: 76, y: 3 },
  { x: 76, y: 68 },
]

const flowPositions = [
  { x: 3, y: 15 },
  { x: 27, y: 15 },
  { x: 51, y: 15 },
  { x: 75, y: 15 },
  { x: 3, y: 65 },
  { x: 27, y: 65 },
  { x: 51, y: 65 },
  { x: 75, y: 65 },
]

const edgeTypeLabels: Record<string, string> = {
  PREREQUISITE_OF: '前置',
  PART_OF: '组成',
  LEARN_AFTER: '后续',
  SUPPORTS: '支持',
  CONTRADICTS: '分歧',
  APPLIES_TO: '应用',
}

export function KnowledgeGraph({ nodes, edges, isLive, onOpen }: KnowledgeGraphProps) {
  const [layout, setLayout] = useState<'constellation' | 'flow'>('constellation')
  const visibleNodes = useMemo(() => nodes.slice(0, 8), [nodes])
  const positions = layout === 'constellation' ? constellationPositions : flowPositions

  const visibleEdges = useMemo<GraphEdge[]>(() => {
    const nodeIds = new Set(visibleNodes.map(node => node.id))
    const usable = edges.filter(edge => nodeIds.has(edge.source) && nodeIds.has(edge.target)).slice(0, 10)
    if (usable.length) return usable
    return visibleNodes.slice(1).map((node, index) => ({
      source: visibleNodes[index].id,
      target: node.id,
      type: index % 2 ? 'SUPPORTS' : 'LEARN_AFTER',
    }))
  }, [edges, visibleNodes])

  const positionById = new Map(visibleNodes.map((node, index) => [node.id, positions[index]]))
  const labelById = new Map(visibleNodes.map(node => [node.id, node.label]))

  return <section className="knowledge-map" aria-label="知识关系方块图">
    <header className="knowledge-map-toolbar">
      <div className="knowledge-map-heading">
        <span className="map-icon"><GitBranch size={17} /></span>
        <div>
          <b>知识星链方块图</b>
          <span>{isLive ? '由 AI 根据知乎内容实时生成' : '从社区观点到行动路径的产品示意'}</span>
        </div>
      </div>
      <button className="layout-switch" onClick={() => setLayout(current => current === 'constellation' ? 'flow' : 'constellation')}>
        {layout === 'constellation' ? <LayoutGrid size={15} /> : <Route size={15} />}
        {layout === 'constellation' ? '切换流程布局' : '切换星链布局'}
      </button>
    </header>

    <div className={`knowledge-map-canvas ${layout}`}>
      <svg className="knowledge-map-lines" viewBox="0 0 1000 500" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <marker id="constellink-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" fill="currentColor" />
          </marker>
        </defs>
        {visibleEdges.map((edge, index) => {
          const source = positionById.get(edge.source)
          const target = positionById.get(edge.target)
          if (!source || !target) return null
          const x1 = source.x * 10 + 105
          const y1 = source.y * 5 + 64
          const x2 = target.x * 10
          const y2 = target.y * 5 + 64
          const bend = Math.max(45, Math.abs(x2 - x1) * .42)
          const path = `M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}`
          return <g key={`${edge.source}-${edge.target}-${index}`}>
            <path className={`map-edge edge-${edge.type.toLowerCase()}`} d={path} markerEnd="url(#constellink-arrow)" />
            {edge.label && <text x={(x1 + x2) / 2} y={(y1 + y2) / 2 - 7}>
              {edge.label.length > 10 ? `${edge.label.slice(0, 10)}…` : edge.label}
            </text>}
          </g>
        })}
      </svg>

      {visibleNodes.map((node, index) => {
        const position = positions[index]
        return <article
          className={`knowledge-block block-${index + 1}`}
          key={node.id}
          style={{ '--map-x': `${position.x}%`, '--map-y': `${position.y}%` } as React.CSSProperties}
        >
          <div className="knowledge-block-top">
            <span>{String(index + 1).padStart(2, '0')}</span>
            <em>{node.category}</em>
          </div>
          <h3>{node.label}</h3>
          <p>{node.description}</p>
          <button onClick={onOpen}>查看观点 <ArrowUpRight size={13} /></button>
        </article>
      })}
    </div>

    <div className="compact-relations" aria-label="知识关系摘要">
      {visibleEdges.slice(0, 6).map((edge, index) => <span key={`${edge.source}-${edge.target}-compact-${index}`}>
        <b>{labelById.get(edge.source)}</b>
        <i>→</i>
        <b>{labelById.get(edge.target)}</b>
        <em>{edge.label || edgeTypeLabels[edge.type] || '关联'}</em>
      </span>)}
    </div>

    <div className="knowledge-map-legend">
      <span><i className="legend-prerequisite" />前置关系</span>
      <span><i className="legend-support" />支持与应用</span>
      <span><i className="legend-disagreement" />观点分歧</span>
      <small><CircleHelp size={14} /> 连线由 AI 返回的知识关系生成</small>
    </div>
  </section>
}
