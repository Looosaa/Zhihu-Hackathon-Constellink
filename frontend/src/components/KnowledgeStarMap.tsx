import { useEffect, useId, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import { ArrowLeft, ArrowRight, ArrowUpRight, LayoutGrid, Orbit, RotateCcw } from 'lucide-react'
import './KnowledgeStarMap.css'

type Node = { id: string; label: string; description: string; category: string }
type Edge = { source: string; target: string; type: string; label?: string }
type Props = { nodes: Node[]; edges: Edge[]; isLive: boolean; onOpen: () => void }
const categories: Record<string, string> = { prerequisite: '前置基础', core: '核心知识', practice: '实践应用', debate: '观点分歧', extension: '延伸探索' }
const relations: Record<string, string> = { PREREQUISITE_OF: '前置', PART_OF: '组成', LEARN_AFTER: '学习顺序', SUPPORTS: '支持', CONTRADICTS: '分歧', APPLIES_TO: '应用' }
const colors = ['#b9c6dd', '#df936c', '#ad99d3', '#e6b678', '#80b6ac', '#799fdc', '#d39cae', '#b0bb8d']
const stars = Array.from({ length: 65 }, (_, i) => ({ x: (i * 137.508 + 19) % 100, y: (i * 71.731 + 13) % 100, opacity: .2 + (i % 5) * .12, size: i % 7 === 0 ? 2 : 1 }))

export function KnowledgeStarMap({ nodes, edges, isLive, onOpen }: Props) {
  const hostRef = useRef<HTMLElement>(null)
  const [compact, setCompact] = useState(false)
  const [view, setView] = useState<'stars' | 'cards'>('stars')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const markerId = `star-arrow-${useId().replace(/:/g, '')}`
  useEffect(() => {
    const element = hostRef.current
    if (!element) return
    const observer = new ResizeObserver(([entry]) => setCompact(entry.contentRect.width < 600))
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  const visibleNodes = nodes.slice(0, 8)
  const validIds = new Set(visibleNodes.map(node => node.id))
  // Orbital guides are decorative; semantic links must come from supplied edges.
  const visibleEdges = edges.filter(edge => edge.source !== edge.target && validIds.has(edge.source) && validIds.has(edge.target))
  const selectedIndex = visibleNodes.findIndex(node => node.id === selectedId)
  const selected = visibleNodes[selectedIndex]
  const labels = new Map(visibleNodes.map(node => [node.id, node.label]))
  const connectedEdges = selected ? visibleEdges.filter(edge => edge.source === selected.id || edge.target === selected.id) : []
  const connectedIds = new Set(connectedEdges.flatMap(edge => [edge.source, edge.target]))
  const width = compact ? 420 : 900
  const height = compact ? 330 + Math.ceil(visibleNodes.length / 2) * 170 : 640
  const earth = compact ? { x: 210, y: 92 } : { x: 450, y: 270 }
  const positions = visibleNodes.map((_, index) => {
    if (compact) return { x: index % 2 === 0 ? 108 : 312, y: 270 + Math.floor(index / 2) * 170 }
    const angle = -Math.PI / 2 + index * Math.PI * 2 / Math.max(visibleNodes.length, 1)
    return { x: 450 + Math.sin(angle) * 320, y: 270 - Math.cos(angle) * 183 }
  })
  const positionById = new Map(visibleNodes.map((node, index) => [node.id, positions[index]]))
  const advance = (offset: number) => {
    const next = Math.max(-1, Math.min(visibleNodes.length - 1, selectedIndex + offset))
    setSelectedId(next < 0 ? null : visibleNodes[next].id)
  }

  return <section className="constellation" ref={hostRef} aria-label="知识星链">
    <header className="cs-toolbar">
      <div className="cs-heading"><span className="cs-heading-icon"><Orbit size={19} /></span><div><h2>知识星链</h2><p>从地球出发，让知识彼此连接</p></div></div>
      <button className="cs-view-switch" onClick={() => setView(view === 'stars' ? 'cards' : 'stars')}>{view === 'stars' ? <LayoutGrid size={15} /> : <Orbit size={15} />}{view === 'stars' ? '方块视图' : '星链视图'}</button>
    </header>
    {view === 'stars' ? <div className="cs-universe">
      <div className="cs-hud"><span><i /> {isLive ? '主题星图' : '示意星图'}</span><span>{visibleNodes.length} 颗知识星球 · {visibleEdges.length} 条关系</span></div>
      <div className="cs-stage" style={{ aspectRatio: `${width} / ${height}` }}>
        <div className="cs-stars" aria-hidden="true">{stars.map((star, i) => <i key={i} style={{ left: `${star.x}%`, top: `${star.y}%`, opacity: star.opacity, width: star.size, height: star.size }} />)}</div>
        <svg className="cs-lines" viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
          <defs><marker id={markerId} markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto-start-reverse"><path d="M0,0 L7,3.5 L0,7" fill="context-stroke" /></marker></defs>
          <g className="cs-orbits"><ellipse cx={width / 2} cy={compact ? height / 2 : 270} rx={compact ? 155 : 325} ry={compact ? height / 2 - 50 : 190} /><ellipse cx={width / 2} cy={compact ? height / 2 : 270} rx={compact ? 105 : 235} ry={compact ? height / 2 - 100 : 134} />{!compact && <ellipse cx="450" cy="270" rx="400" ry="228" />}</g>
          {visibleEdges.map((edge, index) => {
            const from = positionById.get(edge.source)!, to = positionById.get(edge.target)!
            if (edge.source === edge.target) return null
            const dx = to.x - from.x, dy = to.y - from.y, distance = Math.hypot(dx, dy)
            const pad = compact ? 35 : 38
            const x1 = from.x + dx / distance * pad, y1 = from.y + dy / distance * pad
            const x2 = to.x - dx / distance * pad, y2 = to.y - dy / distance * pad
            const bend = Math.min(65, distance * .15) * (index % 2 ? 1 : -1)
            const path = `M${x1},${y1} Q${(x1 + x2) / 2 - dy / distance * bend},${(y1 + y2) / 2 + dx / distance * bend} ${x2},${y2}`
            const active = selected && (edge.source === selected.id || edge.target === selected.id)
            return <path key={`${edge.source}-${edge.target}-${index}`} d={path} markerEnd={`url(#${markerId})`} className={`cs-edge cs-edge-${edge.type.toLowerCase()}${active ? ' is-active' : ''}${selected && !active ? ' is-muted' : ''}`}><title>{labels.get(edge.source)} → {labels.get(edge.target)} · {edge.label || relations[edge.type] || '关联'}</title></path>
          })}
        </svg>
        <button className={`cs-earth${!selected ? ' is-selected' : ''}`} style={{ left: `${earth.x / width * 100}%`, top: `${earth.y / height * 100}%` }} onClick={() => setSelectedId(null)} aria-label="回到地球起点" aria-pressed={!selected}>
          <span className="cs-earth-globe" aria-hidden="true"><svg viewBox="0 0 100 100"><path d="M20 14 37 9 43 19 35 27 44 34 37 46 22 42 17 30ZM34 49 49 52 54 64 45 76 39 87 32 75 28 61ZM58 14 80 21 87 34 72 39 62 33 56 24ZM61 42 75 45 78 57 67 70 59 60ZM78 73 88 71 94 80 82 85Z" /></svg></span><b>地球 · 起点</b><small>你的求知坐标</small>
        </button>
        {visibleNodes.map((node, index) => <button key={node.id} className={`cs-planet${selected?.id === node.id ? ' is-selected' : ''}${connectedIds.has(node.id) ? ' is-connected' : ''}`} style={{ left: `${positions[index].x / width * 100}%`, top: `${positions[index].y / height * 100}%`, '--planet-color': colors[index] } as CSSProperties} onClick={() => setSelectedId(node.id)} aria-pressed={selected?.id === node.id} aria-label={`探索知识星球 ${index + 1}：${node.label}`}>
          <span className={`cs-planet-sphere cs-texture-${index % 4}`} aria-hidden="true">{index === 3 && <i className="cs-saturn-ring" />}<i className="cs-planet-number">{String(index + 1).padStart(2, '0')}</i></span><b title={node.label}>{node.label}</b><small>{categories[node.category] || node.category}</small>
        </button>)}
      </div>
      <div className="cs-space-caption"><span>点击星球，点亮它的知识连接</span><button onClick={() => setSelectedId(null)}><RotateCcw size={13} /> 回到起点</button></div>
    </div> : <div className="cs-card-grid">{visibleNodes.map((node, index) => <button key={node.id} className={`cs-card${selected?.id === node.id ? ' is-selected' : ''}`} onClick={() => setSelectedId(node.id)} aria-pressed={selected?.id === node.id}><span className="cs-card-meta">{String(index + 1).padStart(2, '0')} <em>{categories[node.category] || node.category}</em></span><b>{node.label}</b><p>{node.description}</p><span className="cs-card-link">探索知识点 <ArrowUpRight size={13} /></span></button>)}</div>}
    <div className="cs-inspector" aria-live="polite">
      <div className="cs-inspector-top"><span>{selected ? `正在探索 · ${String(selectedIndex + 1).padStart(2, '0')} / ${String(visibleNodes.length).padStart(2, '0')}` : '从这里出发'}</span><div className="cs-stepper"><button aria-label="上一颗知识星球" disabled={selectedIndex < 0} onClick={() => advance(-1)}><ArrowLeft size={15} /></button><button aria-label="下一颗知识星球" disabled={selectedIndex >= visibleNodes.length - 1} onClick={() => advance(1)}><ArrowRight size={15} /></button></div></div>
      <h3>{selected?.label || '把零散知识，连成你的星图'}</h3><p>{selected?.description || '每颗行星是一个知识点，每条连接线是一段知识关系。从你感兴趣的星球开始，沿着连接探索前置基础、不同观点与实践方向。'}</p>
      {selected && <div className="cs-related">{connectedEdges.length ? connectedEdges.map((edge, index) => {
        const other = edge.source === selected.id ? edge.target : edge.source
        return <button key={`${other}-${index}`} onClick={() => setSelectedId(other)}><span>{edge.source === selected.id ? '→' : '←'} {edge.label || relations[edge.type] || '关联'}</span>{labels.get(other)}</button>
      }) : <span>这个知识点暂时没有已提供的连接。</span>}</div>}
      <button className="cs-explore" onClick={selected ? onOpen : () => advance(1)} disabled={!visibleNodes.length}>{selected ? '查看观点解读' : '出发 · 探索第一站'} <ArrowUpRight size={15} /></button>
    </div>
    <div className="cs-legend"><span><i />前置 / 组成 / 学习顺序</span><span><i className="support" />支持 / 应用</span><span><i className="debate" />分歧</span><small>{isLive ? '关系线来自分析结果 · 点状轨道仅作装饰' : '产品示意 · 不代表已掌握知识'}</small></div>
  </section>
}
