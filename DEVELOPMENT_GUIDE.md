# “知径”AI 学习教练——24 小时黑客松开发文档

> 文档版本：v1.0  
> 更新时间：2026-09-14  
> 适用对象：产品、设计、前端、后端、AI 开发，以及没有技术基础但需要参与协作的同学  
> 项目状态：从零开始，目标是在 24 小时内完成可稳定演示的 MVP

---

## 0. 先读这一页：我们到底要做什么

### 0.1 一句话介绍

“知径”是一个基于知乎多观点内容的 AI 学习教练。用户输入一个想学习的问题，系统从相关知乎内容中提炼共识与分歧，生成可追溯的知识图谱、个性化学习路径，并通过测验和追问帮助用户真正掌握知识。

### 0.2 用户能完成的完整流程

1. 用户输入学习主题，例如“学习机器学习需要先学数学吗？”
2. 用户选择自己的水平、学习目标和每天可投入时间。
3. 系统通过知乎官方数据开放平台搜索相关内容；如果比赛现场无法使用官方接口，则读取团队提前准备并获得授权的演示数据。
4. AI 从不同回答中提取观点、论据、概念和适用人群。
5. 页面展示：
   - 大家普遍同意什么；
   - 不同答主在哪些地方存在分歧；
   - 每种观点适合什么样的人；
   - 每条结论来自哪些作者和原始链接。
6. 系统生成一张可点击的知识图谱。
7. 系统结合用户目标生成 7 天学习计划。
8. 用户完成一道小测验，AI 根据回答给出反馈并更新掌握度。

### 0.3 产品最重要的差异

普通 AI 搜索通常只输出一个综合答案；“知径”刻意保留知乎内容中的多种视角，让用户看见“不同答案为什么不同、分别适合谁”，再把这些观点转化成学习行动。

### 0.4 24 小时内的成功标准

比赛版本只要稳定完成以下闭环，就算成功：

- 能输入一个主题和个人学习信息；
- 能得到 8～15 条带作者和链接的来源；
- 能展示至少 3 条共识和 1 组观点分歧；
- 能展示一张至少 8 个节点的知识图谱；
- 能生成一份 7 天学习计划；
- 能完成至少一道测验并获得反馈；
- 所有 AI 观点都可以追溯到来源；
- 即使知乎 API 临时不可用，演示也能通过本地演示数据完成。

### 0.5 现在不要做的事情

以下功能不属于本次 MVP。除非所有必做功能已验收，否则不要开始：

- 不做自动登录知乎；
- 不做批量爬虫；
- 不做自动发布回答、评论或私信；
- 不做移动端 App；
- 不做复杂的多智能体系统；
- 不做 Neo4j 等独立图数据库；
- 不训练或微调模型；
- 不做复杂推荐算法；
- 不做支付、会员和社交关系；
- 不追求支持任意主题，先保证 1～3 个演示主题稳定。

---

## 1. 给非技术同学的名词解释

| 名词 | 通俗解释 | 在本项目里的作用 |
|---|---|---|
| 前端 | 用户在浏览器里看到和点击的页面 | 输入主题、展示观点、图谱、计划和测验 |
| 后端 | 在服务器上处理数据的程序 | 调用知乎 API、调用大模型、读写数据库 |
| API | 两个软件之间约定好的“传话方式” | 后端通过 API 向知乎和大模型请求数据 |
| 数据库 | 用来长期保存结构化信息的仓库 | 保存学习主题、来源、分析结果和测验记录 |
| Supabase | 带数据库、用户系统和存储能力的云服务 | 本项目主要使用它的 PostgreSQL 数据库 |
| 大模型 / LLM | 能理解和生成文字的 AI 模型 | 提取观点、生成路径、出题和辅导 |
| RAG | 先找资料，再让 AI 根据资料回答 | 减少 AI 凭空编造答案 |
| JSON | 程序之间传递结构化数据的一种格式 | AI 必须按固定 JSON 格式返回分析结果 |
| SSE | 服务器持续向网页发送文字的方式 | 可用于实现回答逐字出现；不是 MVP 必需 |
| 知识图谱 | 用节点和连线表示概念关系 | 展示“先学什么、后学什么、哪些观点冲突” |
| Prompt / 提示词 | 发给大模型的具体任务说明 | 约束 AI 只依据来源生成结构化内容 |
| 环境变量 | 不写进代码的配置和密钥 | 保存数据库地址、API Key、模型名称 |
| MVP | 最小可行产品 | 能完整演示核心价值的最小版本 |

---

## 2. 固定技术方案

为了节省时间，本项目不再比较框架，直接采用以下方案。

### 2.1 前端

- React + TypeScript + Vite
- React Router：页面切换
- TanStack Query：请求后端接口和管理加载状态
- `@xyflow/react`：显示知识图谱
- `react-markdown`：显示 AI 输出中的 Markdown
- `lucide-react`：图标
- 普通 CSS 或一个简单的全局样式文件：24 小时内不引入复杂 UI 框架

### 2.2 后端

- Python 3.11 或更高版本
- FastAPI：提供后端接口
- Uvicorn：运行 FastAPI
- Pydantic：验证输入与 AI 返回的 JSON
- HTTPX：调用知乎 API 和大模型 API
- Supabase Python SDK：读写数据库
- `python-dotenv` / `pydantic-settings`：加载环境变量

### 2.3 数据库

- Supabase PostgreSQL
- MVP 阶段主要使用普通字段和 JSONB 字段
- 暂时不强制实现向量检索
- 如果所有必做功能完成，再使用 `pgvector` 添加语义检索

### 2.4 AI 模型

后端统一接入“OpenAI-compatible”接口。这样只需要修改环境变量就可以切换模型供应商。

至少需要：

- 一个支持中文、能稳定输出 JSON 的对话模型；
- 如果后续实现向量检索，再准备一个 Embedding 模型。

不要在前端直接调用模型。模型 API Key 必须只保存在 Python 后端。

### 2.5 为什么 MVP 暂时不做向量数据库

本次每个主题只处理大约 8～15 条来源。可以先用知乎搜索结果排序，再把经过截断的内容交给大模型分析。这样已经构成“检索后生成”的基本流程，而且能节省至少 2～4 小时。

向量检索只有在以下情况下才是必需的：

- 单次处理数百篇以上内容；
- 用户会持续积累个人知识库；
- 需要从大量历史内容中精准找回片段。

---

## 3. 总体架构

```text
┌──────────────────────────────────────────────┐
│ React 前端                                   │
│ 输入主题 → 观点页 → 知识图谱 → 路径 → 测验   │
└─────────────────────┬────────────────────────┘
                      │ HTTP 请求
                      ▼
┌──────────────────────────────────────────────┐
│ Python FastAPI 后端                          │
│ 参数校验、流程编排、来源编号、错误处理        │
└───────────┬──────────────────┬───────────────┘
            │                  │
            ▼                  ▼
┌───────────────────┐  ┌───────────────────────┐
│ 内容提供器         │  │ 大模型 API             │
│ 1. 知乎官方 API    │  │ 观点抽取、综合、计划、  │
│ 2. Demo 本地数据   │  │ 测验、辅导              │
└───────────┬───────┘  └───────────┬───────────┘
            │                      │
            └──────────┬───────────┘
                       ▼
             ┌─────────────────────┐
             │ Supabase PostgreSQL │
             │ 保存来源与生成结果   │
             └─────────────────────┘
```

架构中的关键设计是“内容提供器可切换”。正式环境使用知乎官方 API，比赛现场如果没有权限、额度耗尽或网络失败，系统自动切换到 Demo 数据，页面和 AI 流程保持不变。

---

## 4. 用户故事与验收标准

### 4.1 创建学习主题

作为学习者，我希望告诉系统“我想学什么、我目前什么水平、我每天有多少时间”，从而得到适合我的内容。

输入字段：

- 学习主题：必填，2～100 个字符；
- 当前水平：小白 / 入门 / 有基础；
- 学习目标：了解概念 / 完成项目 / 面试准备；
- 每日时间：15 / 30 / 60 / 90 分钟；
- 学习天数：MVP 固定为 7 天。

验收：

- 缺少主题时不能提交；
- 点击后立即出现加载状态；
- 分析失败时显示可理解的错误和“重新尝试”按钮；
- 成功后进入结果页。

### 4.2 查看观点地图

作为学习者，我希望快速理解不同答主的共识和分歧。

验收：

- 至少展示 3 条共识；
- 至少展示 1 组 A/B 观点分歧；
- 每个观点显示适用条件；
- 点击来源编号能打开原链接或来源抽屉；
- 不显示无法追溯到来源的事实性结论。

### 4.3 查看知识图谱

作为学习者，我希望看到概念之间的学习顺序。

验收：

- 至少 8 个概念节点；
- 至少包含“前置知识”和“学习顺序”两种边；
- 点击节点显示简短解释和来源；
- 当前需要先学的节点用醒目颜色表示；
- 图谱加载失败时使用列表视图兜底。

### 4.4 查看 7 天学习路径

作为学习者，我希望每天知道要学什么和如何证明自己学会了。

验收：

- 恰好生成 7 天；
- 每天包含目标、内容、行动任务和自测问题；
- 每日预计时间不能明显超过用户选择的时间；
- 学习顺序应遵守知识图谱中的前置关系。

### 4.5 完成互动测验

作为学习者，我希望通过回答问题验证自己是否真的理解。

验收：

- 至少支持一道开放题；
- 用户提交后得到 0～100 分、做得好的地方、需要改进的地方和下一步建议；
- 反馈必须围绕当前学习主题；
- AI 不能因为答案表述不同就直接判错，应判断概念是否正确。

---

## 5. 页面与交互设计

### 5.1 首页 `/`

```text
┌─────────────────────────────────────────────────────┐
│ 知径                                                 │
│ 看见不同答案，找到自己的学习路径                     │
│                                                     │
│ [ 我想学习：学习机器学习需要先学数学吗？          ] │
│                                                     │
│ 当前水平  [小白▼]   学习目标 [完成项目▼]            │
│ 每日时间  [30 分钟▼]                                │
│                                                     │
│                [生成我的学习地图]                   │
│                                                     │
│ 示例：零基础学 Python｜转行产品经理｜理解大模型      │
└─────────────────────────────────────────────────────┘
```

非技术同学负责：首页文字是否在 10 秒内让第一次看到的人理解产品。

### 5.2 分析加载页

不要只显示一个旋转圆圈。按时间轮播以下文字，让用户知道系统正在做什么：

1. “正在寻找知乎中的高质量讨论……”
2. “正在识别不同答主的核心观点……”
3. “正在比较共识、分歧与适用条件……”
4. “正在为你组织知识图谱……”

真实后端可以仍然是一个同步请求，这些提示只用于改善等待体验。

### 5.3 结果页 `/spaces/:id`

页面顶部：

- 学习主题；
- 用户目标标签；
- 一句话总览；
- 来源数量；
- “重新分析”按钮。

页面主体使用四个标签页：

1. 观点地图；
2. 知识图谱；
3. 7 天路径；
4. 互动测验。

### 5.4 观点地图布局

顺序必须是：

1. 一句话总结；
2. 共识卡片；
3. 分歧对比卡；
4. 如何选择；
5. 来源列表。

分歧卡示例：

```text
┌─────────────────────────────────────────────────────┐
│ 分歧：初学机器学习是否应该先系统学习数学？           │
├───────────────────────┬─────────────────────────────┤
│ A：先补数学           │ B：先做项目                 │
│ 理由：建立理论基础     │ 理由：快速获得正反馈         │
│ 适合：学术、算法方向   │ 适合：应用开发、时间有限     │
│ 来源：[S1][S4]        │ 来源：[S2][S3][S7]          │
├───────────────────────┴─────────────────────────────┤
│ AI 建议：若目标是 7 天做出 Demo，先走 B 路线，遇到   │
│ 模型评估问题时再补概率统计。                         │
└─────────────────────────────────────────────────────┘
```

### 5.5 知识图谱颜色

- 蓝色：核心概念；
- 紫色：前置知识；
- 绿色：实践任务；
- 橙色：存在争议的概念；
- 灰色：后续拓展；
- 实线：学习顺序或组成关系；
- 虚线：观点冲突或补充关系。

### 5.6 可访问性与演示稳定性

- 正文字号不小于 16px；
- 浅色背景下保证文字对比度；
- 不要只用颜色表达掌握状态，同时显示文字；
- 图谱必须有列表兜底；
- 所有按钮都有加载和禁用状态；
- 手机尺寸只需不崩溃，不需要专门优化动画。

---

## 6. 项目目录结构

建议建立以下目录：

```text
zhijing/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── ConsensusCard.tsx
│   │   │   ├── DisagreementCard.tsx
│   │   │   ├── KnowledgeGraph.tsx
│   │   │   ├── LearningPlan.tsx
│   │   │   ├── QuizPanel.tsx
│   │   │   └── SourceDrawer.tsx
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   └── LearningSpacePage.tsx
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── styles.css
│   ├── .env.example
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── spaces.py
│   │   │   ├── quizzes.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── errors.py
│   │   ├── models/
│   │   │   ├── requests.py
│   │   │   └── responses.py
│   │   ├── providers/
│   │   │   ├── base.py
│   │   │   ├── zhihu.py
│   │   │   └── demo.py
│   │   ├── services/
│   │   │   ├── ai_gateway.py
│   │   │   ├── analysis.py
│   │   │   ├── learning_plan.py
│   │   │   └── quiz.py
│   │   ├── prompts/
│   │   │   ├── extract_viewpoint.txt
│   │   │   ├── synthesize.txt
│   │   │   ├── create_plan.txt
│   │   │   └── grade_quiz.txt
│   │   ├── repositories/
│   │   │   └── supabase_repo.py
│   │   └── main.py
│   ├── data/
│   │   └── demo_sources.json
│   ├── tests/
│   │   └── test_smoke.py
│   ├── .env.example
│   └── requirements.txt
├── supabase/
│   └── schema.sql
├── DEVELOPMENT_GUIDE.md
└── README.md
```

如果团队只有一位开发者，可以减少文件数量，但要保持“内容提供器”“AI 服务”“接口路由”分开，避免所有代码写在一个文件里后无法排查问题。

---

## 7. 开发环境准备

### 7.1 需要提前注册或准备的服务

负责人逐项确认：

- [ ] 一个 Supabase 项目；
- [ ] 一个可调用中文大模型的 API Key；
- [ ] 知乎开放平台 Access Secret，若暂时没有则启用 Demo 模式；
- [ ] 一个代码仓库；
- [ ] 前后端部署平台，比赛现场也可以先本机运行；
- [ ] 1～3 个稳定演示主题及对应来源数据。

知乎开放平台地址：<https://developer.zhihu.com/>  
官方公开示例使用 Bearer Token 和秒级 `X-Request-Timestamp` 进行鉴权。开放平台仍可能处于邀测或受额度限制状态，不能把比赛演示完全押在实时接口上。

### 7.2 后端依赖

`backend/requirements.txt` 建议内容：

```text
fastapi
uvicorn[standard]
httpx
pydantic
pydantic-settings
python-dotenv
supabase
tenacity
pytest
```

### 7.3 前端依赖

创建 Vite React TypeScript 项目后安装：

```text
react-router-dom
@tanstack/react-query
@xyflow/react
react-markdown
lucide-react
```

### 7.4 环境变量

后端 `.env.example`：

```dotenv
APP_ENV=development
FRONTEND_ORIGIN=http://localhost:5173

SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=replace_me

LLM_BASE_URL=https://YOUR_LLM_PROVIDER/v1
LLM_API_KEY=replace_me
LLM_MODEL=replace_me

CONTENT_PROVIDER=demo
ZHIHU_ACCESS_SECRET=
ZHIHU_API_BASE_URL=https://developer.zhihu.com/api/v1

MAX_SOURCES=12
MAX_SOURCE_CHARS=1200
```

前端 `.env.example`：

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

注意：

- `SUPABASE_SERVICE_ROLE_KEY` 权限很高，只能放后端；
- 不要把真实 `.env` 提交到代码仓库；
- 前端环境变量都会被浏览器用户看到，因此不能放任何秘密；
- 比赛演示前确认部署平台也配置了同样的环境变量。

---

## 8. Supabase 数据库设计

### 8.1 MVP 设计原则

24 小时内优先使用少量表和 JSONB，避免过早把每个概念、观点、关系拆成大量表。知识图谱可以直接从 `analyses.concepts` 和 `analyses.edges` 读取。

### 8.2 可直接执行的建表 SQL

在 Supabase SQL Editor 中执行以下内容：

```sql
create extension if not exists pgcrypto;

create table if not exists learning_spaces (
  id uuid primary key default gen_random_uuid(),
  client_id text not null,
  topic text not null,
  level text not null check (level in ('beginner', 'starter', 'experienced')),
  goal text not null check (goal in ('understand', 'project', 'interview')),
  daily_minutes integer not null check (daily_minutes in (15, 30, 60, 90)),
  status text not null default 'created'
    check (status in ('created', 'analyzing', 'ready', 'failed')),
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  learning_space_id uuid not null references learning_spaces(id) on delete cascade,
  source_key text not null,
  provider text not null check (provider in ('zhihu', 'demo')),
  content_type text not null default 'answer',
  title text not null,
  author_name text not null,
  author_badge text,
  source_url text not null,
  excerpt text not null,
  published_at timestamptz,
  engagement jsonb not null default '{}'::jsonb,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (learning_space_id, source_key)
);

create table if not exists analyses (
  id uuid primary key default gen_random_uuid(),
  learning_space_id uuid not null unique references learning_spaces(id) on delete cascade,
  overview text not null,
  consensus jsonb not null default '[]'::jsonb,
  disagreements jsonb not null default '[]'::jsonb,
  concepts jsonb not null default '[]'::jsonb,
  edges jsonb not null default '[]'::jsonb,
  source_summaries jsonb not null default '[]'::jsonb,
  warnings jsonb not null default '[]'::jsonb,
  model_name text,
  prompt_version text not null default 'v1',
  created_at timestamptz not null default now()
);

create table if not exists study_plans (
  id uuid primary key default gen_random_uuid(),
  learning_space_id uuid not null unique references learning_spaces(id) on delete cascade,
  strategy text not null,
  days jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists quizzes (
  id uuid primary key default gen_random_uuid(),
  learning_space_id uuid not null references learning_spaces(id) on delete cascade,
  concept_id text,
  question text not null,
  reference_answer text not null,
  rubric jsonb not null default '[]'::jsonb,
  source_keys jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists quiz_attempts (
  id uuid primary key default gen_random_uuid(),
  quiz_id uuid not null references quizzes(id) on delete cascade,
  client_id text not null,
  answer text not null,
  score integer check (score between 0 and 100),
  strengths jsonb not null default '[]'::jsonb,
  improvements jsonb not null default '[]'::jsonb,
  next_step text,
  created_at timestamptz not null default now()
);

create table if not exists chat_messages (
  id uuid primary key default gen_random_uuid(),
  learning_space_id uuid not null references learning_spaces(id) on delete cascade,
  client_id text not null,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  citations jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_sources_space on sources(learning_space_id);
create index if not exists idx_quizzes_space on quizzes(learning_space_id);
create index if not exists idx_messages_space on chat_messages(learning_space_id, created_at);

alter table learning_spaces enable row level security;
alter table sources enable row level security;
alter table analyses enable row level security;
alter table study_plans enable row level security;
alter table quizzes enable row level security;
alter table quiz_attempts enable row level security;
alter table chat_messages enable row level security;
```

本版本只允许持有 Service Role Key 的后端访问数据库，所以启用 RLS 后不创建前端直连策略。前端只能通过 FastAPI 访问数据。

### 8.3 JSON 字段示例

`consensus`：

```json
[
  {
    "id": "consensus_1",
    "title": "项目实践应该尽早开始",
    "detail": "多数来源认为，初学者不需要等所有理论都掌握后再实践。",
    "source_keys": ["S1", "S3", "S6"]
  }
]
```

`disagreements`：

```json
[
  {
    "id": "disagreement_1",
    "question": "是否需要先系统学习数学？",
    "side_a": {
      "title": "先补数学",
      "reason": "理论基础有助于理解算法边界。",
      "suitable_for": ["算法研究", "时间充足"],
      "source_keys": ["S1", "S4"]
    },
    "side_b": {
      "title": "先做项目",
      "reason": "快速反馈可以降低入门门槛。",
      "suitable_for": ["应用开发", "时间有限"],
      "source_keys": ["S2", "S3"]
    },
    "how_to_choose": "以完成应用为目标时先实践，以研究算法为目标时先补数学。"
  }
]
```

`concepts` 与 `edges`：

```json
{
  "concepts": [
    {
      "id": "python",
      "label": "Python 基础",
      "category": "prerequisite",
      "description": "能够阅读和修改基础 Python 代码。",
      "source_keys": ["S2", "S5"]
    },
    {
      "id": "ml_project",
      "label": "机器学习项目",
      "category": "practice",
      "description": "完成从数据清洗到模型评估的小项目。",
      "source_keys": ["S2", "S3"]
    }
  ],
  "edges": [
    {
      "source": "python",
      "target": "ml_project",
      "type": "PREREQUISITE_OF",
      "label": "前置知识"
    }
  ]
}
```

---

## 9. 后端 API 约定

所有响应都使用 JSON。错误响应统一格式：

```json
{
  "error": {
    "code": "LLM_INVALID_JSON",
    "message": "AI 返回格式异常，请重新尝试。",
    "retryable": true
  }
}
```

### 9.1 健康检查

`GET /health`

成功响应：

```json
{
  "status": "ok",
  "content_provider": "demo",
  "database": "connected",
  "llm": "configured"
}
```

注意：健康检查不需要真的调用一次大模型，以免浪费时间和额度，只检查配置是否存在。

### 9.2 创建学习空间

`POST /api/spaces`

请求：

```json
{
  "client_id": "browser-generated-id",
  "topic": "学习机器学习需要先学数学吗？",
  "level": "beginner",
  "goal": "project",
  "daily_minutes": 30
}
```

响应：

```json
{
  "id": "UUID",
  "status": "created"
}
```

### 9.3 执行分析

`POST /api/spaces/{space_id}/analyze`

MVP 使用同步处理。调用可能需要 15～60 秒，前端必须保持加载状态，不要重复提交。

响应结构：

```json
{
  "space": {
    "id": "UUID",
    "topic": "学习机器学习需要先学数学吗？",
    "status": "ready"
  },
  "sources": [],
  "analysis": {
    "overview": "……",
    "consensus": [],
    "disagreements": [],
    "concepts": [],
    "edges": [],
    "warnings": []
  }
}
```

### 9.4 获取完整结果

`GET /api/spaces/{space_id}?client_id=...`

返回学习空间、来源、分析、计划和已生成测验。刷新页面后依靠这个接口恢复状态。

### 9.5 生成学习计划

`POST /api/spaces/{space_id}/plan`

响应：

```json
{
  "strategy": "先实践建立整体认识，再按问题补充前置知识。",
  "days": [
    {
      "day": 1,
      "title": "认识完整流程",
      "goal": "理解机器学习项目包含哪些步骤",
      "concept_ids": ["ml_workflow"],
      "activities": ["阅读观点 S2", "画出自己的流程图"],
      "output": "一张包含 5 个步骤的流程图",
      "self_check": "训练集和测试集为什么需要分开？",
      "estimated_minutes": 30
    }
  ]
}
```

### 9.6 生成测验

`POST /api/spaces/{space_id}/quizzes`

请求可选：

```json
{
  "concept_id": "overfitting"
}
```

响应不能把 `reference_answer` 发给前端，只返回：

```json
{
  "id": "UUID",
  "concept_id": "overfitting",
  "question": "请用一个生活中的例子解释什么是过拟合。",
  "source_keys": ["S1", "S5"]
}
```

### 9.7 提交测验答案

`POST /api/quizzes/{quiz_id}/attempts`

请求：

```json
{
  "client_id": "browser-generated-id",
  "answer": "过拟合就像把练习题答案背下来……"
}
```

响应：

```json
{
  "score": 82,
  "strengths": ["例子体现了记忆训练数据这一特点"],
  "improvements": ["还可以说明为什么面对新数据表现会下降"],
  "next_step": "尝试比较过拟合与欠拟合。"
}
```

### 9.8 可选：互动追问

`POST /api/spaces/{space_id}/chat`

只在必做功能完成后开发。第一版使用普通 JSON 返回，不必为了逐字输出增加 SSE 风险。

---

## 10. 内容接入设计

### 10.1 统一数据格式

无论数据来自知乎 API 还是本地 Demo，进入 AI 分析前都转换为以下格式：

```json
{
  "source_key": "S1",
  "provider": "zhihu",
  "content_type": "answer",
  "title": "问题或文章标题",
  "author_name": "作者名",
  "author_badge": "认证信息，可为空",
  "source_url": "https://www.zhihu.com/...",
  "excerpt": "用于分析的正文片段",
  "published_at": null,
  "engagement": {
    "upvotes": 0,
    "comments": 0
  }
}
```

### 10.2 内容提供器接口

逻辑示意：

```python
from typing import Protocol

class ContentProvider(Protocol):
    async def search(self, query: str, limit: int) -> list[dict]:
        """搜索并返回统一格式的来源。"""
```

根据环境变量选择：

```python
if settings.content_provider == "zhihu":
    provider = ZhihuProvider(...)
else:
    provider = DemoProvider(...)
```

### 10.3 知乎官方 API 调用要点

官方公开示例：

- 请求地址：`GET https://developer.zhihu.com/api/v1/content/zhihu_search`
- Query 参数：`Query=用户主题`
- 请求头：`Authorization: Bearer <Access Secret>`
- 请求头：`X-Request-Timestamp: 秒级 Unix 时间戳`
- 请求头：`Content-Type: application/json`

HTTPX 调用示意：

```python
import time
import httpx

async def search_zhihu(query: str, secret: str) -> dict:
    headers = {
        "Authorization": f"Bearer {secret}",
        "X-Request-Timestamp": str(int(time.time())),
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(
            "https://developer.zhihu.com/api/v1/content/zhihu_search",
            params={"Query": query},
            headers=headers,
        )
        response.raise_for_status()
        return response.json()
```

重要：官方返回字段可能随实际账号权限和接口版本变化。拿到 Access Secret 后，第一件事是保存一份脱敏响应样例，再根据真实字段完成 `normalize_zhihu_payload()`。不要根据猜测写死字段。

### 10.4 Demo 数据方案

`backend/data/demo_sources.json` 必须至少准备：

- 1 个主要演示主题；
- 8～12 条来源；
- 至少两种明显不同的观点；
- 每条来源包含作者名、标题、原链接和 500～1200 字符的授权或合理使用片段；
- 不包含付费墙后的全文、隐私资料或未经允许的大段复制内容。

为了保证演示稳定，可以额外缓存该主题的最终分析结果：

```text
demo_sources.json       原始来源
demo_analysis.json      已生成的观点与图谱
demo_plan.json          已生成的 7 天计划
```

推荐三级降级策略：

1. 知乎 API + 实时 AI；
2. Demo 来源 + 实时 AI；
3. Demo 来源 + 已缓存 AI 结果。

第三层保证即使比赛现场模型 API 超时，核心页面仍能展示。

### 10.5 来源筛选规则

来源进入 AI 前进行简单处理：

1. 去掉完全重复的 URL；
2. 去掉没有正文或正文太短的结果；
3. 每条最多保留 `MAX_SOURCE_CHARS` 个字符；
4. 保留标题、作者、认证和互动数据；
5. 给来源编号 `S1`、`S2`……；
6. 最多使用 `MAX_SOURCES` 条；
7. 优先保证观点多样性，而不是全部选择表达同一立场的高赞回答。

---

## 11. AI 分析流水线

### 11.1 总流程

```text
用户主题
  ↓
搜索 8～15 条来源
  ↓
清洗、截断、编号
  ↓
逐来源抽取观点（可并行）
  ↓
综合共识与分歧
  ↓
生成概念节点与关系
  ↓
Pydantic 校验 JSON
  ↓
保存数据库并返回前端
```

### 11.2 为什么先逐篇抽取再综合

如果直接把所有正文交给 AI 要求总结，模型容易忽略少数观点或把不同作者的观点混在一起。逐篇抽取能保留每条观点与来源的对应关系，第二步再做综合。

### 11.3 失败重试规则

- 网络超时：最多重试 2 次；
- HTTP 429：等待后重试 1 次；
- AI JSON 解析失败：把校验错误发回模型修复 1 次；
- 第二次仍失败：切换缓存结果或向前端返回可重试错误；
- 不要无限重试，避免比赛现场一直卡住。

### 11.4 成本与速度控制

- 每条来源截断到 800～1200 个中文字符；
- 最多使用 12 条来源；
- 逐篇抽取可用较便宜的模型；
- 综合、路径和评分使用能力更强的模型；
- 相同学习空间重复打开时直接读取数据库；
- 相同 Demo 主题优先使用缓存。

---

## 12. AI 输出结构与提示词

提示词应放在单独文本文件中，并写 `prompt_version`。修改提示词时不要直接覆盖比赛前已经验证稳定的版本。

### 12.1 逐来源观点抽取提示词

文件：`backend/app/prompts/extract_viewpoint.txt`

```text
你是学习内容分析员。你的任务是从一条来源中提取作者真正表达的观点，不能使用来源之外的知识。

规则：
1. 只依据给定正文，不补充未出现的事实。
2. 保留作者的条件、限制和不确定性。
3. evidence 必须是正文中的短片段或忠实转述，不得编造。
4. 如果正文与用户主题关系很弱，relevance_score 应低于 0.4。
5. 输出合法 JSON，不要输出 Markdown，不要解释 JSON。

用户学习主题：{{topic}}
来源编号：{{source_key}}
来源标题：{{title}}
作者：{{author_name}}
正文：
{{excerpt}}

输出结构：
{
  "source_key": "S1",
  "relevance_score": 0.0,
  "position_summary": "作者核心立场，不超过60字",
  "claims": [
    {
      "text": "具体观点",
      "evidence": "支持这一观点的正文依据",
      "confidence": 0.0
    }
  ],
  "concepts": [
    {
      "name": "概念名称",
      "definition": "作者语境下的简短解释"
    }
  ],
  "suitable_for": ["这一观点适合的人或情境"],
  "limitations": ["作者提到或正文可直接推出的限制"]
}
```

### 12.2 综合观点与知识图谱提示词

文件：`backend/app/prompts/synthesize.txt`

```text
你是一个严谨的 AI 学习教练。请根据多条已经结构化的知乎来源，帮助用户看见共识、分歧和学习顺序。

用户信息：
- 主题：{{topic}}
- 水平：{{level}}
- 目标：{{goal}}
- 每日时间：{{daily_minutes}} 分钟

来源分析：
{{source_analyses_json}}

必须遵守：
1. 只能使用来源分析中存在的信息。
2. 所有共识、立场和概念都必须列出 source_keys。
3. 至少两个相互独立的来源支持时，才称为“共识”；否则称为“单一观点”。
4. 不要为了制造戏剧性而虚构分歧。
5. 分歧必须说明双方理由、适用人群以及如何选择。
6. 概念 ID 使用简短的小写英文或拼音，下划线连接，不能重复。
7. 边的 source 和 target 必须引用 concepts 中存在的 ID。
8. 关系类型只能是 PREREQUISITE_OF、PART_OF、LEARN_AFTER、SUPPORTS、CONTRADICTS、APPLIES_TO。
9. 最终输出合法 JSON，不输出 Markdown 或额外解释。

输出结构：
{
  "overview": "面向用户的一句话总览",
  "consensus": [
    {
      "id": "consensus_1",
      "title": "共识标题",
      "detail": "共识解释",
      "source_keys": ["S1", "S2"]
    }
  ],
  "disagreements": [
    {
      "id": "disagreement_1",
      "question": "分歧问题",
      "side_a": {
        "title": "立场 A",
        "reason": "理由",
        "suitable_for": ["人群或场景"],
        "source_keys": ["S1"]
      },
      "side_b": {
        "title": "立场 B",
        "reason": "理由",
        "suitable_for": ["人群或场景"],
        "source_keys": ["S2"]
      },
      "how_to_choose": "结合用户目标给出的选择建议"
    }
  ],
  "concepts": [
    {
      "id": "concept_id",
      "label": "概念名",
      "category": "core|prerequisite|practice|debate|extension",
      "description": "不超过80字",
      "source_keys": ["S1"]
    }
  ],
  "edges": [
    {
      "source": "concept_a",
      "target": "concept_b",
      "type": "PREREQUISITE_OF",
      "label": "前置知识"
    }
  ],
  "warnings": ["来源不足、内容过时或观点不确定时的提示"]
}
```

### 12.3 7 天计划提示词

文件：`backend/app/prompts/create_plan.txt`

```text
你是个性化学习规划师。请根据用户信息、观点分析和知识图谱生成恰好 7 天的学习计划。

用户信息：{{user_profile_json}}
观点与图谱：{{analysis_json}}

要求：
1. 每天预计时间不得超过用户每日时间的 110%。
2. 前置概念必须安排在依赖它的概念之前。
3. 每天都必须有一个可观察的输出，而不是只写“阅读”。
4. 每天都必须有一个自测问题。
5. source_keys 只能引用已有来源。
6. 第 7 天必须包含回顾和综合输出。
7. 输出合法 JSON，不输出额外解释。

输出：
{
  "strategy": "为什么这样安排",
  "days": [
    {
      "day": 1,
      "title": "当天主题",
      "goal": "可验证的目标",
      "concept_ids": ["concept_id"],
      "activities": ["具体行动"],
      "source_keys": ["S1"],
      "output": "当天必须产出的东西",
      "self_check": "自测问题",
      "estimated_minutes": 30
    }
  ]
}
```

### 12.4 测验评分提示词

文件：`backend/app/prompts/grade_quiz.txt`

```text
你是耐心但严格的学习教练。请根据评分标准判断用户是否理解概念，而不是检查是否逐字匹配参考答案。

题目：{{question}}
评分标准：{{rubric_json}}
参考答案：{{reference_answer}}
用户答案：{{user_answer}}

规则：
1. 总分为 0～100 的整数。
2. 优先指出用户已经做对的部分。
3. 改进建议必须具体且不超过 3 条。
4. 如果答案包含明显错误，指出错误但不要羞辱用户。
5. 不引入与题目无关的新知识。
6. 输出合法 JSON，不输出额外说明。

输出：
{
  "score": 0,
  "strengths": ["做得好的地方"],
  "improvements": ["需要改进的地方"],
  "next_step": "下一步练习建议"
}
```

### 12.5 AI JSON 校验

后端必须使用 Pydantic 校验：

- `source_keys` 是否都存在；
- 概念 ID 是否唯一；
- 边是否引用存在的节点；
- 计划是否恰好 7 天；
- 每日时间是否合理；
- 分数是否在 0～100；
- 必填文字是否为空。

验证失败时，不要把错误 JSON 直接存数据库或传给前端。

---

## 13. 前端数据类型

前后端必须共享相同概念。TypeScript 示例：

```ts
export type Source = {
  source_key: string;
  title: string;
  author_name: string;
  author_badge?: string | null;
  source_url: string;
  excerpt: string;
};

export type Consensus = {
  id: string;
  title: string;
  detail: string;
  source_keys: string[];
};

export type GraphConcept = {
  id: string;
  label: string;
  category: "core" | "prerequisite" | "practice" | "debate" | "extension";
  description: string;
  source_keys: string[];
};

export type GraphEdge = {
  source: string;
  target: string;
  type:
    | "PREREQUISITE_OF"
    | "PART_OF"
    | "LEARN_AFTER"
    | "SUPPORTS"
    | "CONTRADICTS"
    | "APPLIES_TO";
  label: string;
};
```

前端不要自行猜测缺失字段。后端负责把所有供应商数据转换成稳定响应。

---

## 14. 前端实现重点

### 14.1 浏览器身份

MVP 不做登录。首次访问时生成一个随机 `client_id` 并保存到 `localStorage`。创建空间、读取结果和提交测验时都携带它。

这是比赛演示方案，不是正式生产用户系统。正式上线时应替换为 Supabase Auth。

### 14.2 请求状态

每个请求至少处理四种状态：

- 未开始；
- 加载中；
- 成功；
- 失败。

加载时禁用按钮，失败时显示重试。不要让用户连续点击产生多个分析任务。

### 14.3 来源引用组件

页面中统一使用 `[S1]`、`[S2]` 标签。点击后打开来源抽屉，显示：

- 作者；
- 认证信息；
- 标题；
- 摘要片段；
- “查看知乎原文”按钮。

来源 URL 必须来自后端，不允许 AI 自己生成 URL。

### 14.4 知识图谱组件

把后端 `concepts` 转换为 React Flow nodes，把 `edges` 转换为 React Flow edges。

第一版不需要自动布局算法，可以按 category 分列：

- 前置知识：左侧；
- 核心概念：中间；
- 实践与拓展：右侧；
- 争议节点：下方。

如果布局来不及，使用简单网格坐标。稳定比完美更重要。

### 14.5 图谱兜底

如果 React Flow 报错或节点为零，显示概念卡片列表，不允许整个页面空白。

### 14.6 设计建议

- 主色：知乎蓝附近的蓝色，但不要使用知乎 Logo，也不要暗示官方产品；
- 背景：浅灰或偏暖白；
- 卡片：白底、细边框、轻阴影；
- 分歧 A/B 使用不同浅色背景，不使用“正确/错误”红绿对立；
- 页脚注明“AI 生成内容仅供学习参考，观点可回溯至原来源；本项目非知乎官方产品”。

---

## 15. 后端编排逻辑

`POST /api/spaces/{id}/analyze` 的推荐顺序：

```text
1. 检查 client_id 是否拥有该学习空间
2. 把状态改为 analyzing
3. 调用当前 ContentProvider 搜索来源
4. 来源不足 3 条时尝试 DemoProvider
5. 清洗、截断、编号并保存 sources
6. 逐来源调用观点抽取
7. 删除 relevance_score 过低的结果
8. 调用综合提示词生成共识、分歧和图谱
9. 用 Pydantic 校验并修复一次
10. 保存 analyses
11. 状态改为 ready
12. 返回来源和分析结果
```

任何异常都要：

1. 写入服务器日志；
2. 将空间状态改为 `failed`；
3. 保存适合用户阅读的 `error_message`；
4. 不向前端暴露 API Key、数据库连接或完整堆栈。

建议错误码：

| 错误码 | 用户看到的信息 | 是否可重试 |
|---|---|---|
| `CONTENT_UNAVAILABLE` | 暂时没有找到足够的学习来源 | 是 |
| `ZHIHU_AUTH_FAILED` | 内容服务授权暂不可用，已尝试演示模式 | 是 |
| `LLM_TIMEOUT` | AI 分析超时，请重新尝试 | 是 |
| `LLM_INVALID_JSON` | AI 返回格式异常，请重新尝试 | 是 |
| `SPACE_NOT_FOUND` | 没有找到这个学习主题 | 否 |
| `DATABASE_ERROR` | 保存结果失败，请稍后重试 | 是 |

---

## 16. 24 小时执行计划

### 16.1 默认三人分工

| 角色 | 主要职责 | 不能等待别人完成的准备工作 |
|---|---|---|
| A：后端与 AI | FastAPI、数据库、内容提供器、模型调用、提示词 | 先用静态 JSON 完成接口，不等真实知乎 API |
| B：前端 | 首页、结果页、观点卡、图谱、路径、测验 | 先用 mock JSON 开发，不等后端 |
| C：产品与数据 | Demo 来源、文案、视觉规范、测试、路演 | 立即整理演示数据和测试用例，不等页面 |

如果只有两个人：A 负责后端与 AI，B 负责前端，同时由 B 整理 Demo 数据。  
如果只有一个人：严格按“静态页面 → Demo 数据 → AI → 数据库 → 真实 API”的顺序，不要先攻克知乎接入。

### 16.2 逐小时计划

#### 第 0～1 小时：锁定范围

- [ ] 所有人阅读本文档第 0、4、16、19 节；
- [ ] 确定唯一主要演示主题；
- [ ] 创建代码仓库和任务看板；
- [ ] 分配 A/B/C 负责人；
- [ ] 创建 Supabase 项目；
- [ ] 验证大模型 Key 能返回一句中文；
- [ ] 检查知乎 Access Secret；
- [ ] 明确没有 Secret 就使用 Demo 数据，不继续等待。

交付物：团队能用一句话复述产品，且每个人知道自己未来 5 小时的任务。

#### 第 1～3 小时：跑通骨架

后端：

- [ ] FastAPI `/health` 可以访问；
- [ ] 执行数据库 SQL；
- [ ] 建好请求和响应 Pydantic 模型；
- [ ] DemoProvider 能读 `demo_sources.json`。

前端：

- [ ] 首页可输入主题；
- [ ] 结果页四个标签可以切换；
- [ ] 使用 mock 数据显示至少一张共识卡和一张分歧卡。

产品：

- [ ] 完成 8～12 条演示来源；
- [ ] 为来源分配 S1～S12；
- [ ] 标出预期共识和分歧，供 AI 结果人工核对。

里程碑：前后端都能独立启动。

#### 第 3～6 小时：内容与 AI 抽取

- [ ] 大模型网关可调用；
- [ ] 单条来源可以返回合法观点 JSON；
- [ ] Pydantic 能拦截错误输出；
- [ ] 8～12 条来源全部完成抽取；
- [ ] 综合提示词返回共识、分歧、概念和关系；
- [ ] 保存一份成功输出作为缓存。

里程碑：后端用 Demo 数据能返回完整分析 JSON。

#### 第 6～10 小时：核心页面

- [ ] 首页连接创建与分析接口；
- [ ] 加载页能显示阶段提示；
- [ ] 结果页显示 overview；
- [ ] 共识卡显示来源标签；
- [ ] A/B 分歧卡显示适用人群；
- [ ] 来源抽屉能打开原链接；
- [ ] 错误状态可以重试。

里程碑：用户能从首页走到观点地图。

#### 第 10～13 小时：知识图谱

- [ ] 后端概念和边通过验证；
- [ ] React Flow 显示节点；
- [ ] 节点按类型着色；
- [ ] 点击节点显示解释和来源；
- [ ] 增加列表兜底。

里程碑：图谱可看、可点，刷新不丢失。

#### 第 13～16 小时：学习路径和测验

- [ ] 生成恰好 7 天计划；
- [ ] 每天包含目标、行动、输出和自测；
- [ ] 页面显示 7 天时间线；
- [ ] 能生成一道开放题；
- [ ] 能提交答案并得到评分反馈。

里程碑：完整学习闭环首次跑通。

#### 第 16～18 小时：接入真实知乎 API（有权限才做）

- [ ] 保存一份脱敏 API 响应；
- [ ] 完成字段归一化；
- [ ] 处理超时和鉴权错误；
- [ ] 失败时自动切换 DemoProvider；
- [ ] 页面能显示当前数据来源模式。

如果第 16 小时仍没有 Access Secret，跳过本阶段，转去测试和美化。

#### 第 18～20 小时：联调和异常处理

- [ ] 新建、分析、刷新、生成计划、答题全部测试；
- [ ] 测试模型返回非法 JSON；
- [ ] 测试模型超时；
- [ ] 测试来源不足；
- [ ] 测试数据库暂时失败；
- [ ] 测试手机宽度不出现严重错位；
- [ ] 确认控制台没有阻断性报错。

#### 第 20～22 小时：视觉和路演

- [ ] 统一字号、颜色和按钮；
- [ ] 准备 90 秒和 3 分钟两个版本的演示稿；
- [ ] 录制一份完整操作视频；
- [ ] 准备 5 张关键页面截图；
- [ ] 所有成员至少演练一次；
- [ ] 计时并删除不必要的讲解。

#### 第 22～24 小时：冻结与缓冲

- [ ] 停止增加功能；
- [ ] 设置默认 Demo 模式；
- [ ] 备份成功缓存；
- [ ] 在比赛使用的电脑上完整跑一遍；
- [ ] 检查网络断开时是否仍能展示核心结果；
- [ ] 创建最终版本标签或压缩包；
- [ ] 除致命错误外不再改核心代码。

---

## 17. 测试清单

### 17.1 核心流程冒烟测试

每次合并代码后至少执行：

1. 打开首页；
2. 输入主要演示主题；
3. 选择小白、完成项目、每日 30 分钟；
4. 点击生成；
5. 查看至少 3 条共识；
6. 打开一条来源；
7. 查看一组分歧；
8. 切换到知识图谱并点击节点；
9. 切换到 7 天路径；
10. 生成测验并提交答案；
11. 刷新浏览器，结果仍存在。

### 17.2 AI 结果人工检查

非技术同学也能完成：

- [ ] 共识是否真的由至少两个来源支持；
- [ ] AI 是否把作者没说过的话归给作者；
- [ ] 分歧双方是否真的不同；
- [ ] “适合谁”是否有合理依据；
- [ ] 来源标签是否能对应到正确作者；
- [ ] 知识图谱有没有断开的孤立节点；
- [ ] 学习顺序有没有明显倒置；
- [ ] 7 天计划能否在每日限制时间内完成；
- [ ] 测验反馈是否具体而非套话。

### 17.3 异常测试

- 空主题；
- 只有一个字的主题；
- 200 字超长主题；
- 知乎 API 401；
- 知乎 API 超时；
- 模型 API 429；
- 模型返回 Markdown 代码块而非纯 JSON；
- 数据库写入失败；
- 来源 URL 为空；
- 图谱边引用不存在的节点；
- 用户重复点击生成按钮。

---

## 18. 演示方案

### 18.1 推荐主题

主要主题：

> “零基础学习机器学习，需要先系统学习数学吗？”

选择它的原因：

- 存在天然的两种观点；
- 容易提取前置知识和学习顺序；
- 容易生成知识图谱；
- 评委即使不懂机器学习，也能理解“先理论还是先实践”的冲突；
- 可以自然生成个性化建议。

备选主题：

- “产品经理如何系统学习大模型应用开发？”
- “零基础学 Python 应该先看课程还是直接做项目？”

### 18.2 三分钟演示脚本

#### 0:00～0:25：问题

“在知乎搜索一个学习问题，我们会看到很多高质量回答，但不同答主的建议经常不一样。用户不是缺少答案，而是不知道这些答案为什么不同、哪个更适合自己。”

#### 0:25～0:50：输入

输入“学习机器学习需要先学数学吗”，选择“小白”“想完成项目”“每天 30 分钟”。

#### 0:50～1:35：观点地图

展示共识，再重点展示“先补数学”和“先做项目”的分歧。点击 S1/S2，证明每条观点可以回到作者和原始内容。

#### 1:35～2:05：知识图谱

展示 Python、数学、模型训练、评估和项目之间的关系。点击一个节点，展示解释和来源。

#### 2:05～2:35：7 天路径

强调系统没有给所有人同一张路线图，而是根据“完成项目、每天 30 分钟”安排了先实践、按需补理论的路径。

#### 2:35～2:50：测验

回答一道开放题，展示 AI 如何判断理解程度并给出下一步练习。

#### 2:50～3:00：总结

“搜索引擎帮你找到答案，知径帮助你看懂不同答案为什么不同，并把答案变成真正可以学会的路径。”

### 18.3 演示现场保护措施

- 默认使用已经验证的 Demo 主题；
- 提前打开页面完成一次预热；
- 缓存完整分析、路径和测验；
- 准备操作视频；
- 准备截图版路演稿；
- 关闭可能弹出通知的软件；
- 不在现场展示 API Key、后台日志或数据库管理页；
- 不临时输入高风险、医学、法律或政治主题。

---

## 19. 功能优先级与砍功能顺序

### P0：必须完成

- 首页输入；
- Demo 内容提供器；
- AI 共识与分歧；
- 来源引用；
- 知识图谱或其列表兜底；
- 7 天计划；
- 一道测验；
- 结果缓存；
- 完整演示脚本。

### P1：完成 P0 后再做

- 真实知乎 API；
- React Flow 更好的布局；
- 多道测验；
- 普通对话式辅导；
- SSE 流式输出；
- Supabase Auth。

### P2：赛后功能

- pgvector；
- 收藏夹或个人知识库；
- 长期掌握度曲线；
- 间隔重复复习；
- 多主题知识网络；
- 创作者订阅和更新提醒；
- 多模态内容；
- 完整运营与审核后台。

如果时间不足，按以下顺序删除：

1. 删除聊天；
2. 删除动画；
3. 删除真实知乎 API，使用 DemoProvider；
4. 把知识图谱降级为有层级的概念列表；
5. 测验固定为一道预生成问题；
6. 计划使用缓存结果。

不能删除观点分歧、来源引用和个性化学习路径，因为它们是产品的核心价值。

---

## 20. 常见问题排查

### 20.1 前端显示“网络错误”

依次检查：

1. 后端 `/health` 是否能打开；
2. `VITE_API_BASE_URL` 是否正确；
3. 后端 CORS 是否允许前端地址；
4. 部署环境是否仍写着 `localhost`；
5. 浏览器开发者工具 Network 中的实际状态码。

### 20.2 数据库连接失败

检查：

- `SUPABASE_URL` 是否完整；
- 使用的是 Service Role Key 而不是前端 anon key；
- 表是否已经执行 SQL 创建；
- 字段名是否和代码一致；
- 是否错误地从前端直接访问启用了 RLS 的表。

### 20.3 AI 经常返回非法 JSON

处理顺序：

1. 确认提示词明确要求只输出 JSON；
2. 去掉模型返回外层的 Markdown 代码块；
3. 使用 JSON response format（供应商支持时）；
4. 减少一次输出的字段数量；
5. 把 Pydantic 错误发给模型修复一次；
6. 演示主题切换到缓存结果。

### 20.4 知识图谱空白

检查：

- `concepts` 是否为空；
- edge 的 source/target 是否存在；
- 节点是否有 position；
- React Flow 外层容器是否有明确高度；
- CSS 是否把文字和背景设成同色；
- 出错时是否显示列表兜底。

### 20.5 分析速度太慢

- 来源从 12 条减到 8 条；
- 每条正文从 1200 字符减到 800 字符；
- 逐来源抽取并发执行，但限制并发为 3～5；
- Demo 主题直接加载预生成的单篇抽取结果；
- 不在同一次请求中同时生成计划和测验；
- 页面先展示观点，计划由用户切换标签时再生成。

### 20.6 模型额度耗尽

- 切换备用模型 Key；
- 启用缓存分析；
- 测验反馈使用预生成案例；
- 现场只演示固定主题；
- 不反复点击重新分析。

---

## 21. 安全、版权和合规

### 21.1 数据来源

- 优先使用知乎官方数据开放平台；
- 不使用登录 Cookie 批量获取内容；
- 不绕过付费内容权限；
- 不采集私信、联系方式、个人收藏或非公开资料；
- Demo 数据应来自团队有权使用的内容，并保留原链接和作者信息。

### 21.2 内容展示

- 每条观点展示具体来源；
- 不在自己的页面重新发布大段全文；
- 摘要必须忠实，不歪曲作者原意；
- AI 生成内容注明“仅供学习参考”；
- 医疗、法律、投资等高风险主题在 MVP 中提示用户查阅专业来源；
- 不把社区互动数量直接等同于内容绝对正确。

### 21.3 密钥和用户数据

- 所有密钥只在后端；
- 日志不能打印完整请求头；
- 不记录用户提交的敏感个人信息；
- 正式上线前增加身份认证、限流、数据删除入口和隐私说明；
- 如果用户内容会发送给第三方模型，应在页面告知。

### 21.4 品牌

- 不使用知乎 Logo；
- 不写“知乎官方”“知乎合作产品”，除非已获得授权；
- 页面注明“本项目非知乎官方产品”；
- 产品描述可以写“基于知乎公开或授权内容构建”。

---

## 22. 上线与部署检查

### 22.1 后端

- 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port 8000`
- 生产环境不能使用自动重载；
- 配置前端正式域名到 CORS；
- 设置模型请求超时；
- 至少保留错误级别日志；
- `/health` 可从公网访问；
- 不公开 Swagger 中的敏感示例数据。

### 22.2 前端

- `VITE_API_BASE_URL` 指向正式后端；
- 刷新 `/spaces/:id` 不返回 404；
- 外部来源链接使用新标签页；
- 页面标题和 favicon 已设置；
- 浏览器控制台没有明显错误；
- 1366×768 投影分辨率下关键内容可见。

### 22.3 比赛电脑

- 浏览器已登录必要账号，但不展示后台；
- 充电器和网络热点就绪；
- 本地前后端也能作为备用方案运行；
- 演示视频存本地；
- 缓存 JSON 存本地；
- 路演文稿有 PDF 备份；
- 至少两个人知道如何从首页完成演示。

---

## 23. 最终完成定义（Definition of Done）

提交前，产品负责人逐项勾选。任何一项失败都比增加新功能更优先修复。

- [ ] 新用户能在 10 秒内理解产品用途；
- [ ] 输入主题后 60 秒内得到结果，或使用缓存快速返回；
- [ ] 页面至少展示 8 条真实、可打开的来源；
- [ ] 共识都有两个及以上来源支持；
- [ ] 分歧双方都有来源；
- [ ] AI 没有编造作者和 URL；
- [ ] 知识图谱至少有 8 个节点；
- [ ] 图谱失败时有列表兜底；
- [ ] 7 天计划符合用户每日时间；
- [ ] 至少一道测验可完成并评分；
- [ ] 刷新页面不会丢失核心结果；
- [ ] 知乎 API 不可用时可以切换 Demo；
- [ ] 大模型不可用时可以加载缓存；
- [ ] 真实密钥没有提交到仓库；
- [ ] 页面包含 AI 与非官方产品声明；
- [ ] 3 分钟演示完成至少两次计时彩排；
- [ ] 有本地演示视频和截图备份。

---

## 24. 赛后演进路线

比赛后如果继续开发，按以下顺序扩展：

### 第一阶段：让学习结果真正可持续

- Supabase Auth；
- 学习进度和概念掌握度；
- 错题记录；
- 间隔重复复习；
- 用户手动纠正 AI 提取的观点。

### 第二阶段：扩大内容规模

- `pgvector` 语义检索；
- 混合检索：关键词 + 向量 + 社区信号；
- 内容去重和时效性评分；
- 增量更新来源；
- 多主题知识库。

### 第三阶段：连接知乎社区价值

- 关注专业创作者和主题更新；
- 展示观点随时间发生的变化；
- 识别“共识形成过程”；
- 引导用户带着更高质量的问题回到原内容讨论；
- 在获得明确授权后探索创作者工具。

---

## 25. 参考资料

- 知乎数据开放平台：<https://developer.zhihu.com/>
- 知乎投资者关系与公司信息：<https://ir.zhihu.com/cn/corporate-information/>
- 知乎 2025 年中期报告：<https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0910/2025091000263_c.pdf>
- 知乎个人信息保护相关页面：<https://www.zhihu.com/term/old-privacy-5-1>

---

## 附录 A：团队每日站会模板

在 24 小时比赛中，每 3 小时进行一次 5 分钟同步。每人只回答：

1. 我刚完成了什么可见结果？
2. 接下来 3 小时我会交付什么？
3. 我现在被什么阻塞？
4. 如果时间不足，我会删除什么？

禁止用“快好了”描述进度。应使用“接口已经返回 mock JSON”“观点卡已经显示真实来源”这样可验证的表达。

## 附录 B：提交材料建议

最终提交包建议包含：

- README：项目简介和运行方法；
- 本开发文档；
- 架构图；
- 90 秒产品视频；
- 3 分钟完整演示视频；
- 5 张产品截图；
- 测试账号或无需登录的演示地址；
- 免责声明；
- 团队成员与分工；
- 后续商业化或生态合作设想。

## 附录 C：一句话决策原则

遇到意见分歧时使用以下顺序决策：

1. 能不能让“多观点学习”更清晰？
2. 能不能在比赛现场稳定展示？
3. 能不能在剩余时间内完成并测试？
4. 是否保留作者和来源可追溯性？

如果答案不是明确的“能”，本次就不做。
