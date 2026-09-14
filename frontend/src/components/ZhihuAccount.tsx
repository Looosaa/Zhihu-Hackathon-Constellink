import { useCallback, useEffect, useRef, useState } from 'react'
import { ChevronDown, LogOut, UserRound, X } from 'lucide-react'
import './ZhihuAccount.css'
import './ZhihuAccountDemo.css'

type User = {
  id: string
  name: string
  avatar_url: string
  headline: string
  description: string
}

type UserItem = {
  id?: string
  name?: string
  avatar_url?: string
  headline?: string
  url: string
  title?: string
  summary?: string
  follower_count?: number
  like_count?: number
}

type Page = {
  items: UserItem[]
  has_more: boolean
  next_offset: string | null
  total: number
}

export function ZhihuAccount() {
  const [user, setUser] = useState<User | null>(null)
  const [available, setAvailable] = useState(false)
  const [demoMode, setDemoMode] = useState(false)
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [error, setError] = useState(() => new URLSearchParams(window.location.search).has('login_error')
    ? '知乎授权未完成，请稍后重试。'
    : '')
  const trigger = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    const controller = new AbortController()
    const query = new URLSearchParams(window.location.search)
    const shouldOpen = query.get('account') === '1'
    if (shouldOpen || query.has('login_error')) {
      query.delete('account')
      query.delete('login_error')
      const suffix = query.size ? `?${query.toString()}` : ''
      window.history.replaceState(null, '', `${window.location.pathname}${suffix}${window.location.hash}`)
    }
    fetch('/api/auth/session', { credentials: 'include', signal: controller.signal })
      .then(async response => {
        if (!response.ok) throw new Error('无法读取登录状态')
        return response.json() as Promise<{
          user: User | null
          login_available: boolean
          oauth_demo_mode: boolean
        }>
      })
      .then(data => {
        setUser(data.user)
        setAvailable(data.login_available)
        setDemoMode(data.oauth_demo_mode)
        setOpen(shouldOpen && Boolean(data.user))
      })
      .catch(reason => {
        if (reason instanceof Error && reason.name !== 'AbortError') setError(reason.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [])

  const close = () => {
    setOpen(false)
    requestAnimationFrame(() => trigger.current?.focus())
  }

  const logout = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      })
      if (!response.ok) throw new Error('退出失败，请重试。')
      setUser(null)
      close()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '退出失败，请重试。')
    } finally {
      setLoading(false)
    }
  }

  return <div className="zh-account">
    {user ? <button ref={trigger} className="zh-account-trigger" onClick={() => setOpen(true)} aria-haspopup="dialog">
      <Avatar src={user.avatar_url} name={user.name} />
      <span>{user.name}</span>
      <ChevronDown size={14} />
    </button> : <button
      className="zh-account-login"
      disabled={loading || !available}
      title={!loading && !available ? '请先在后端配置 OAuth 回调地址' : undefined}
      onClick={() => window.location.assign('/api/auth/zhihu/login')}
    >
      <UserRound size={16} />
      {loading ? '读取中' : available ? '知乎登录' : '登录待配置'}
    </button>}
    {error && <span role="alert" className="zh-account-error">{error}</span>}
    {open && user && <AccountDialog
      user={user}
      demoMode={demoMode}
      onClose={close}
      onLogout={logout}
      onExpired={() => {
        setUser(null)
        setOpen(false)
        setError('登录已过期，请重新登录。')
      }}
    />}
  </div>
}

function Avatar({ src, name }: { src?: string; name: string }) {
  const [failed, setFailed] = useState(false)
  return src && !failed
    ? <img className="zh-account-avatar" src={src} alt="" referrerPolicy="no-referrer" onError={() => setFailed(true)} />
    : <span className="zh-account-avatar zh-account-initial">{name.slice(0, 1)}</span>
}

function AccountDialog({ user, demoMode, onClose, onLogout, onExpired }: {
  user: User
  demoMode: boolean
  onClose: () => void
  onLogout: () => void
  onExpired: () => void
}) {
  const dialog = useRef<HTMLDialogElement>(null)
  const [tab, setTab] = useState<'followees' | 'contents'>('followees')

  useEffect(() => dialog.current?.showModal(), [])

  return <dialog ref={dialog} className="zh-account-dialog" aria-labelledby="account-title" onCancel={onClose}>
    <header>
      <h2 id="account-title">个人中心</h2>
      <button className="zh-icon-button" onClick={onClose} aria-label="关闭个人中心"><X size={18} /></button>
    </header>
    <section className="zh-account-profile">
      <Avatar src={user.avatar_url} name={user.name} />
      <div><h3>{user.name}</h3><p>{user.headline || '这位知友还没有填写一句话介绍。'}</p></div>
    </section>
    {demoMode && <p className="zh-account-demo-notice">
      黑客松演示登录：知乎当前回调可能不返回 state，暂不作为生产级登录使用。
    </p>}
    {user.description && <p className="zh-account-description">{user.description}</p>}
    <nav className="zh-account-tabs" aria-label="用户内容分类">
      <button aria-pressed={tab === 'followees'} onClick={() => setTab('followees')}>关注的人</button>
      <button aria-pressed={tab === 'contents'} onClick={() => setTab('contents')}>创作信息</button>
    </nav>
    <AccountList key={tab} resource={tab} onExpired={onExpired} />
    <footer><button className="zh-logout" onClick={onLogout}><LogOut size={15} />退出登录</button></footer>
  </dialog>
}

function AccountList({ resource, onExpired }: {
  resource: 'followees' | 'contents'
  onExpired: () => void
}) {
  const [page, setPage] = useState<Page>({ items: [], has_more: false, next_offset: null, total: 0 })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [retryOffset, setRetryOffset] = useState('0')
  const active = useRef<AbortController | null>(null)

  const load = useCallback(async (offset: string) => {
    if (active.current) return
    const controller = new AbortController()
    active.current = controller
    setBusy(true)
    setError('')
    setRetryOffset(offset)
    try {
      const response = await fetch(`/api/me/${resource}?limit=20&offset=${encodeURIComponent(offset)}`, {
        credentials: 'include',
        signal: controller.signal,
      })
      if (response.status === 401) {
        onExpired()
        return
      }
      if (!response.ok) throw new Error('暂时无法读取，请稍后重试。')
      const result = await response.json() as Page
      setPage(previous => ({
        ...result,
        items: offset === '0' ? result.items : [...previous.items, ...result.items],
      }))
    } catch (reason) {
      if (reason instanceof Error && reason.name !== 'AbortError') setError(reason.message)
    } finally {
      if (!controller.signal.aborted) {
        active.current = null
        setBusy(false)
      }
    }
  }, [onExpired, resource])

  useEffect(() => {
    const task = window.setTimeout(() => void load('0'), 0)
    return () => {
      window.clearTimeout(task)
      active.current?.abort()
      active.current = null
    }
  }, [load])

  const label = resource === 'followees' ? '关注用户' : '创作内容'
  return <section className="zh-account-list" aria-busy={busy} aria-live="polite">
    <p className="zh-account-count">已加载 {page.items.length} 条 · 共 {page.total} 条</p>
    {page.items.map((item, index) => <article key={`${item.url}-${index}`}>
      {resource === 'followees' && <Avatar src={item.avatar_url} name={item.name || '知友'} />}
      <div>
        {item.url
          ? <a href={item.url} target="_blank" rel="noopener noreferrer">{item.name || item.title}</a>
          : <strong>{item.name || item.title}</strong>}
        <p>{item.headline || item.summary || '暂无介绍'}</p>
        <small>{resource === 'followees' ? `${item.follower_count || 0} 人关注` : `${item.like_count || 0} 次赞同`}</small>
      </div>
    </article>)}
    {!busy && !error && page.items.length === 0 && <p className="zh-account-empty">暂无可展示的{label}。</p>}
    {error && <p role="alert" className="zh-list-error">{error} <button onClick={() => load(retryOffset)}>重试</button></p>}
    {busy
      ? <p className="zh-account-empty">正在加载…</p>
      : page.has_more && !error && page.next_offset !== null
        ? <button className="zh-load-more" onClick={() => load(page.next_offset!)}>加载更多</button>
        : null}
  </section>
}
