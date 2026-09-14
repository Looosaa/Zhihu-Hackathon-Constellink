import { useMemo, useState } from 'react'
import { Bell, BookOpen, ChevronRight, CircleHelp, Clock3, LayoutGrid, LoaderCircle, MoreHorizontal, Play, Plus, Search, Sparkles, X } from 'lucide-react'
import { analyzeLearningSpace, createLearningSpace, createQuiz, createStudyPlan, getLearningSpace, submitQuizAttempt } from './api/client'
import { ZhihuAccount } from './components/ZhihuAccount'
import type { CompleteLearningSpace, Grade, LearningGoal, LearnerLevel, Quiz } from './types'
import './App.css'

type RequestState = 'idle' | 'creating' | 'analyzing' | 'loading' | 'success' | 'error'
type Tab = '图谱' | '列表' | '详细介绍' | '来源'

const fallbackNodes = [
  { id: '01', label: '为什么要建立知识图谱？', description: '从零散信息到结构化理解，先找到知识之间的关系。', category: '示例' },
  { id: '02', label: '从知乎观点中提炼共识', description: '识别不同回答中的共同观点、事实和关键依据。', category: '示例' },
  { id: '03', label: '理解分歧与适用场景', description: '同一个问题为什么有不同答案？如何判断适合自己的路径。', category: '示例' },
  { id: '04', label: '生成你的学习路径', description: '把概念、前置知识和实践任务组织成可执行计划。', category: '示例' },
]

function App() {
  const [tab, setTab] = useState<Tab>('图谱')
  const [composer, setComposer] = useState(false)
  const [topic, setTopic] = useState('')
  const [level, setLevel] = useState<LearnerLevel>('beginner')
  const [goal, setGoal] = useState<LearningGoal>('understand')
  const [minutes, setMinutes] = useState<15 | 30 | 60 | 90>(30)
  const [state, setState] = useState<RequestState>('idle')
  const [error, setError] = useState('')
  const [spaceId, setSpaceId] = useState('')
  const [result, setResult] = useState<CompleteLearningSpace | null>(null)
  const [planState, setPlanState] = useState<'idle' | 'loading' | 'done' | 'error'>('idle')
  const [quiz, setQuiz] = useState<Quiz | null>(null)
  const [quizState, setQuizState] = useState<'idle' | 'loading' | 'ready' | 'submitting' | 'done' | 'error'>('idle')
  const [answer, setAnswer] = useState('')
  const [feedback, setFeedback] = useState<Grade | null>(null)

  const graphNodes = useMemo(() => result?.analysis?.concepts.slice(0, 8) ?? fallbackNodes, [result])
  const busy = ['creating', 'analyzing', 'loading'].includes(state)

  const submitSpace = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!topic.trim() || busy) return
    setError('')
    setResult(null)
    setPlanState('idle')
    setQuiz(null)
    setFeedback(null)
    setState('creating')
    try {
      const space = await createLearningSpace({ topic: topic.trim(), level, goal, dailyMinutes: minutes })
      setSpaceId(space.id)
      setState('analyzing')
      await analyzeLearningSpace(space.id)
      setState('loading')
      setResult(await getLearningSpace(space.id))
      setState('success')
      setComposer(false)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '请求失败')
      setState('error')
    }
  }

  const makePlan = async () => {
    if (!spaceId) return
    setPlanState('loading')
    try {
      const plan = await createStudyPlan(spaceId)
      setResult(previous => previous ? { ...previous, plan } : previous)
      setPlanState('done')
    } catch {
      setPlanState('error')
    }
  }

  const makeQuiz = async () => {
    if (!spaceId) return
    setQuizState('loading')
    try {
      setQuiz(await createQuiz(spaceId))
      setQuizState('ready')
    } catch {
      setQuizState('error')
    }
  }

  const answerQuiz = async () => {
    if (!quiz?.id || !answer.trim()) return
    setQuizState('submitting')
    try {
      setFeedback(await submitQuizAttempt(quiz.id, answer))
      setQuizState('done')
    } catch {
      setQuizState('error')
    }
  }

  return <div className="site">
    <Header onCreate={() => setComposer(true)} />
    <main className="page">
      <div className="breadcrumbs">图谱 <ChevronRight size={14} /> AI 学习基础 <ChevronRight size={14} /> 当前图谱</div>
      <section className="title-row">
        <div>
          <div className="kicker"><Sparkles size={15} /> AI 学习路径</div>
          <h1>{result?.space.topic || '如何构建你的知识学习路径'}</h1>
          <p className="subtitle">{result?.analysis?.overview || '从知乎真实讨论出发，理解观点、建立连接，找到适合自己的学习方法。'}</p>
          <div className="meta">
            <span><BookOpen size={15} /> {result?.analysis?.concepts.length ?? 4} 个知识节点</span>
            <span>{result?.sources.length ?? 0} 个知乎来源</span>
            <span className="status-dot"><i /> {state === 'success' ? '分析完成' : busy ? '正在分析' : '等待创建'}</span>
          </div>
        </div>
        <button className="continue-button" onClick={() => setComposer(true)}><Play size={16} fill="currentColor" /> 创建学习空间</button>
      </section>

      <div className="content-layout">
        <section className="main-card">
          <div className="tabs">
            {(['图谱', '列表', '详细介绍', '来源'] as Tab[]).map(item => <button
              className={tab === item ? 'tab active' : 'tab'} key={item} onClick={() => setTab(item)}
            >{item}{item === '来源' && result ? ` · ${result.sources.length}` : ''}</button>)}
          </div>

          {tab === '图谱' && <>
            <div className="graph-toolbar"><div><b>知识关系</b><span>{result ? '来自真实 AI 分析结果' : '创建学习空间后展示真实知识节点'}</span></div><button className="toolbar-button"><LayoutGrid size={15} /> 自动布局</button></div>
            <div className="graph-canvas">{graphNodes.map((node, index) => <div className="node-wrap" key={node.id}>
              <article className={`learning-node ${result ? 'active' : index < 2 ? 'done' : index === 2 ? 'active' : 'locked'}`}>
                <div className="node-top"><span className="node-number">{String(index + 1).padStart(2, '0')}</span><span className="node-status active">{node.category}</span></div>
                <h3>{node.label}</h3><p>{node.description}</p>
                <button className="node-action" onClick={() => setTab('详细介绍')}>查看分析 <ChevronRight size={14} /></button>
              </article>
              {index < graphNodes.length - 1 && <div className="connector"><ChevronRight size={18} /></div>}
            </div>)}</div>
            <div className="graph-help"><CircleHelp size={15} /> 当前版本按 AI 返回顺序展示；知识关系详见分析结果</div>
          </>}

          {tab === '列表' && <div className="result-panel"><h2>知识点列表</h2>
            {result?.analysis?.concepts.length ? result.analysis.concepts.map(item => <article className="result-item" key={item.id}><span>{item.category}</span><div><h3>{item.label}</h3><p>{item.description}</p></div></article>) : <EmptyResult />}
          </div>}

          {tab === '详细介绍' && <div className="result-panel"><h2>观点提炼</h2>
            {result?.analysis ? <><p className="overview-copy">{result.analysis.overview}</p><h3>主要共识</h3>
              {result.analysis.consensus.map(item => <article className="insight-card consensus" key={item.id}><b>{item.title}</b><p>{item.detail}</p><small>来源：{item.source_keys.join('、')}</small></article>)}
              <h3>观点分歧</h3>{result.analysis.disagreements.map(item => <article className="insight-card disagreement" key={item.id}><b>{item.question}</b><p>{item.side_a.title}：{item.side_a.reason}</p><p>{item.side_b.title}：{item.side_b.reason}</p><small>如何选择：{item.how_to_choose}</small></article>)}
            </> : <EmptyResult />}
          </div>}

          {tab === '来源' && <div className="result-panel"><h2>知乎内容来源</h2>
            {result?.sources.length ? result.sources.map(source => <article className="source-item" key={source.source_key}><b>{source.source_key}</b><div><a href={source.source_url} target="_blank" rel="noopener noreferrer">{source.title}</a><p>{source.author_name} · {source.excerpt}</p></div></article>) : <EmptyResult />}
          </div>}
        </section>

        <aside className="sidebar">
          <div className="progress-card"><div className="progress-ring"><strong>{result ? 25 : 0}<small>%</small></strong></div><div><b>学习进度</b><p>{result ? '分析完成，可以生成计划' : '创建学习空间后开始'}</p></div></div>
          <section className="side-section"><div className="side-title"><h2>学习概览</h2><MoreHorizontal size={18} /></div><div className="stat-list">
            <div><span>每日学习时间</span><b>{result?.space.daily_minutes ?? minutes} 分钟</b></div><div><span>知识节点</span><b>{result?.analysis?.concepts.length ?? 0} 个</b></div><div><span>观点分歧</span><b>{result?.analysis?.disagreements.length ?? 0} 个</b></div>
          </div></section>
          <section className="side-section"><div className="side-title"><h2>下一步</h2></div>
            <button className="side-action" onClick={makePlan} disabled={!spaceId || planState === 'loading'}>{planState === 'loading' ? '正在生成学习计划…' : result?.plan ? '重新生成学习计划' : '生成 7 天学习计划'}</button>
            {planState === 'error' && <p className="side-error">学习计划生成失败，请重试。</p>}
            {result?.plan && <div className="plan-preview"><p>{result.plan.strategy}</p>{result.plan.days.map(day => <div key={day.day}><b>第 {day.day} 天 · {day.title}</b><span>{day.estimated_minutes} 分钟</span></div>)}</div>}
            <button className="side-action" onClick={makeQuiz} disabled={!spaceId || quizState === 'loading'}>{quizState === 'loading' ? '正在生成测验…' : '生成知识测验'}</button>
            {quizState === 'error' && <p className="side-error">测验处理失败，请重试。</p>}
            {quiz && <div className="quiz-box"><b>{quiz.question}</b><textarea value={answer} onChange={event => setAnswer(event.target.value)} placeholder="输入你的答案…" rows={3} /><button className="side-action" onClick={answerQuiz} disabled={quizState !== 'ready'}>{quizState === 'submitting' ? '评分中…' : '提交答案'}</button>{feedback && <p className="feedback">得分：{feedback.score}<br />{feedback.next_step}</p>}</div>}
          </section>
        </aside>
      </div>
    </main>
    <footer>liank · 让知识学习更有路径</footer>
    {composer && <Composer topic={topic} setTopic={setTopic} level={level} setLevel={setLevel} goal={goal} setGoal={setGoal} minutes={minutes} setMinutes={setMinutes} state={state} error={error} busy={busy} onSubmit={submitSpace} onClose={() => !busy && setComposer(false)} />}
  </div>
}

function Header({ onCreate }: { onCreate: () => void }) {
  return <header className="header"><div className="header-inner"><div className="brand"><span className="brand-symbol"><Sparkles size={17} /></span><b>liank</b></div><nav><a className="active">图谱</a><a>刷知识</a><a>AI 助手</a></nav><div className="header-search"><Search size={16} /><input placeholder="搜索图谱、笔记、知识点…" /></div><div className="header-actions"><button><Clock3 size={17} /><span>复习</span></button><button className="notice"><Bell size={17} /><i>2</i></button><button className="create" onClick={onCreate}><Plus size={16} /> 创作</button><ZhihuAccount /></div></div></header>
}

function EmptyResult() {
  return <div className="tab-placeholder"><BookOpen size={28} /><h2>等待分析结果</h2><p>点击右上方“创建学习空间”开始真实前后端流程。</p></div>
}

function Composer(props: { topic: string; setTopic: (value: string) => void; level: LearnerLevel; setLevel: (value: LearnerLevel) => void; goal: LearningGoal; setGoal: (value: LearningGoal) => void; minutes: 15 | 30 | 60 | 90; setMinutes: (value: 15 | 30 | 60 | 90) => void; state: RequestState; error: string; busy: boolean; onSubmit: (event: React.FormEvent) => void; onClose: () => void }) {
  const label = props.state === 'creating' ? '正在创建学习空间…' : props.state === 'analyzing' ? 'AI 正在分析，可能需要 2～5 分钟…' : props.state === 'loading' ? '正在读取完整结果…' : '开始真实分析'
  return <div className="modal-backdrop"><section className="composer-modal"><button className="modal-close" onClick={props.onClose} aria-label="关闭"><X size={18} /></button><div className="kicker"><Sparkles size={15} /> 创建真实学习空间</div><h2>你想学习什么？</h2><p className="modal-desc">将检索知乎内容，并通过 AI 生成观点、知识图谱和学习路径。</p><form onSubmit={props.onSubmit}>
    <label>学习主题<textarea value={props.topic} onChange={event => props.setTopic(event.target.value)} placeholder="例如：我想系统学习机器学习，并完成一个项目" rows={3} required /></label>
    <div className="composer-grid"><label>你的水平<select value={props.level} onChange={event => props.setLevel(event.target.value as LearnerLevel)}><option value="beginner">入门了解</option><option value="starter">有一些基础</option><option value="experienced">已经有经验</option></select></label><label>学习目标<select value={props.goal} onChange={event => props.setGoal(event.target.value as LearningGoal)}><option value="understand">理解概念</option><option value="project">完成项目</option><option value="interview">准备面试</option></select></label><label>每日时间<select value={props.minutes} onChange={event => props.setMinutes(Number(event.target.value) as 15 | 30 | 60 | 90)}><option value={15}>15 分钟</option><option value={30}>30 分钟</option><option value={60}>60 分钟</option><option value={90}>90 分钟</option></select></label></div>
    {props.error && <div className="request-error">{props.error}<small>请确认 FastAPI 与网络服务正常。</small></div>}
    {props.state === 'analyzing' && <div className="analysis-progress"><LoaderCircle size={17} className="spin" /><div><b>正在生成 AI 分析</b><span>检索知乎内容 → 提炼观点 → 生成知识图谱</span></div></div>}
    <button className="modal-submit" disabled={props.busy}>{props.busy && <LoaderCircle size={16} className="spin" />}{label}</button>
  </form></section></div>
}

export default App
