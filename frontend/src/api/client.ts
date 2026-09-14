import type { CompleteLearningSpace, Grade, LearningSpaceInput, Quiz, StudyPlan } from '../types'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')
const CLIENT_ID_KEY = 'constellink_client_id'

/** 浏览器首次访问时创建，并在后续请求中保持同一个 client_id。 */
export function getClientId(): string {
  const existing = localStorage.getItem(CLIENT_ID_KEY)
  if (existing && existing.length >= 16) return existing
  const clientId = crypto.randomUUID()
  localStorage.setItem(CLIENT_ID_KEY, clientId)
  return clientId
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers: { ...(options.body ? { 'Content-Type': 'application/json' } : {}), ...options.headers },
  })
  if (!response.ok) {
    let message = `请求失败（${response.status}）`
    try {
      const payload = await response.json() as { detail?: unknown; error?: { message?: string } }
      if (typeof payload.detail === 'string') message = payload.detail
      else if (Array.isArray(payload.detail)) message = payload.detail.map((item) => typeof item === 'object' && item !== null && 'msg' in item ? String(item.msg) : String(item)).join('；')
      else if (payload.error?.message) message = payload.error.message
    } catch { /* 非 JSON 错误响应使用默认提示 */ }
    throw new Error(message)
  }
  return response.json() as Promise<T>
}

export interface ApiEnvelope<T> {
  data: T
  meta?: { request_id?: string; execution_mode?: string }
}

interface CreatedSpace { id: string; topic: string; status: 'created' | 'analyzing' | 'ready' | 'failed' }

/** 1. 创建学习空间 */
export async function createLearningSpace(input: LearningSpaceInput) {
  const response = await request<ApiEnvelope<CreatedSpace>>('/api/spaces', {
    method: 'POST',
    body: JSON.stringify({
      client_id: getClientId(),
      topic: input.topic,
      level: input.level,
      goal: input.goal,
      daily_minutes: input.dailyMinutes,
    }),
  })
  return response.data
}

/** 2. 生成 AI 分析。后端要求 client_id 放在 JSON body 中。 */
export async function analyzeLearningSpace(spaceId: string) {
  const response = await request<ApiEnvelope<{ space_id: string; status: 'accepted' }>>(`/api/spaces/${spaceId}/analyze`, {
    method: 'POST',
    body: JSON.stringify({ client_id: getClientId(), force: false }),
  })
  return response.data
}

/** 轮询后台分析，避开 CloudBase 单次 HTTP 请求 60 秒的硬限制。 */
export async function waitForLearningSpace(
  spaceId: string,
  options: { timeoutMs?: number; intervalMs?: number } = {},
) {
  const timeoutMs = options.timeoutMs ?? 4 * 60 * 1000
  const intervalMs = options.intervalMs ?? 2000
  const deadline = Date.now() + timeoutMs
  let lastNetworkError: unknown = null

  while (Date.now() < deadline) {
    let result: CompleteLearningSpace | null = null
    try {
      result = await getLearningSpace(spaceId)
      lastNetworkError = null
    } catch (reason) {
      lastNetworkError = reason
    }
    if (result?.space.status === 'ready' && result.analysis) return result
    if (result?.space.status === 'failed') {
      throw new Error(result.space.error_message || 'AI 分析失败，请重新尝试。')
    }
    await new Promise(resolve => window.setTimeout(resolve, intervalMs))
  }

  if (lastNetworkError instanceof Error) throw lastNetworkError
  throw new Error('AI 分析仍在进行，请稍后重试。')
}

/** 3. 读取完整结果 */
export async function getLearningSpace(spaceId: string) {
  const response = await request<ApiEnvelope<CompleteLearningSpace>>(`/api/spaces/${spaceId}?client_id=${encodeURIComponent(getClientId())}`)
  return response.data
}

/** 4. 生成学习计划。后端要求 client_id 放在 JSON body 中。 */
export async function createStudyPlan(spaceId: string) {
  const response = await request<ApiEnvelope<StudyPlan>>(`/api/spaces/${spaceId}/plan`, {
    method: 'POST',
    body: JSON.stringify({ client_id: getClientId(), force: false }),
  })
  return response.data
}

/** 5. 生成测验。后端要求 client_id 放在 JSON body 中。 */
export async function createQuiz(spaceId: string, conceptId?: string) {
  const response = await request<ApiEnvelope<Quiz>>(`/api/spaces/${spaceId}/quizzes`, {
    method: 'POST',
    body: JSON.stringify({ client_id: getClientId(), concept_id: conceptId ?? null }),
  })
  return response.data
}

/** 6. 提交答案并评分。 */
export async function submitQuizAttempt(quizId: string, answer: string) {
  const response = await request<ApiEnvelope<Grade>>(`/api/quizzes/${quizId}/attempts`, {
    method: 'POST',
    body: JSON.stringify({ client_id: getClientId(), answer }),
  })
  return response.data
}
