# “知径”后端开发流程与架构手册

> 文档版本：v1.0  
> 更新时间：2026-09-14  
> 配套文档：[DEVELOPMENT_GUIDE.md](./DEVELOPMENT_GUIDE.md)  
> 目标：在不到 24 小时内完成结构清晰、可以稳定演示、以后也能继续扩展的 Python 后端

---

## 0. 先做决定：后端最终采用什么结构

本项目采用“轻量分层架构”，固定为以下五层：

```text
API 接口层
    ↓
业务用例层 Services
    ↓
领域模型与接口契约 Domain / Ports
    ↓
外部适配器 Providers / Repositories
    ↓
知乎 API、大模型 API、Supabase、本地 Demo 文件
```

最重要的规则：

> 业务逻辑只能依赖“抽象接口”，不能直接依赖知乎、某个模型供应商或 Supabase 的具体写法。

这样设计后：

- 知乎 API 不可用：只替换内容提供器；
- 模型供应商变化：只替换 LLM 适配器；
- Supabase 改为 MySQL：只替换 Repository；
- Demo 数据改成实时数据：业务流程不用改；
- 前端接口保持稳定：内部重构不会影响前端。

### 0.1 本次后端必须完成的模块

- FastAPI 应用入口；
- 统一配置、日志、异常和请求 ID；
- 学习空间管理；
- 内容提供器接口；
- Demo 内容提供器；
- 知乎内容提供器骨架及可选真实接入；
- OpenAI-compatible 大模型适配器；
- 观点抽取与综合编排；
- 7 天学习计划；
- 测验生成与评分；
- Supabase 数据访问；
- 分析结果缓存和三级降级；
- 单元测试、契约测试和冒烟测试。

### 0.2 本次不引入的架构复杂度

- 不使用微服务；
- 不使用消息队列；
- 不使用 Celery；
- 不使用 Kubernetes；
- 不使用独立图数据库；
- 不使用 LangChain 等大型编排框架；
- 不建立复杂的通用 Agent；
- 不为 8～15 条来源强行实现向量检索；
- 不在 Route 中直接写业务逻辑。

一个 FastAPI 服务足够。架构清晰不等于框架越多越好。

---

## 1. 架构必须长期保持的六条规则

### 规则一：接口层只负责 HTTP

Route 只能做：

- 接收参数；
- 调用 Service；
- 返回响应；
- 声明状态码。

Route 不能做：

- 拼 Prompt；
- 调用大模型；
- 解析知乎字段；
- 直接操作 Supabase；
- 实现降级逻辑；
- 包含长段 `try/except`。

### 规则二：Service 负责编排，不负责供应商细节

Service 知道“需要搜索内容、抽取观点、保存结果”，但不知道：

- 知乎鉴权头怎么写；
- 模型接口 URL 是什么；
- Supabase SDK 如何查询；
- Demo JSON 文件放在哪里。

这些细节全部在适配器里。

### 规则三：所有外部数据先归一化

知乎 API、Demo 文件和未来其他来源，进入业务层前都必须转换成统一的 `RetrievedSource`。

大模型的所有返回值，也必须先通过 Pydantic 校验再进入业务层。

### 规则四：数据库模型不是 API 模型

不要把 Supabase 返回的字典原样传给前端。数据库结构、内部领域结构和前端响应分别定义，必要时显式转换。

### 规则五：依赖只向内，不反向

允许：

```text
api → services → domain
providers → domain
repositories → domain
```

禁止：

```text
domain → FastAPI
domain → Supabase
services → 某个具体 ZhihuProvider
services → 某个具体 OpenAICompatibleLLM
```

### 规则六：先建立契约，再填实现

第一轮先创建所有目录、领域模型、接口和空实现，让程序能启动。然后逐层填充逻辑。不要写完一个巨大文件后再拆。

---

## 2. 一次性创建的目录结构

后端目录固定如下。后续尽量只向已有目录添加文件，不重新改变整体结构。

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # 创建 FastAPI 应用
│   ├── container.py               # 组装具体依赖
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py        # Route 使用的 Depends
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── spaces.py
│   │       └── quizzes.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # 环境变量
│   │   ├── errors.py              # 业务异常
│   │   ├── error_handlers.py      # 异常转 HTTP 响应
│   │   ├── logging.py             # 结构化日志
│   │   └── middleware.py          # request_id、耗时等
│   │
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── enums.py               # 枚举
│   │   ├── entities.py            # 内部领域模型
│   │   ├── analysis_models.py     # AI 分析结果模型
│   │   └── ports.py               # Provider/Repository 抽象接口
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── common.py              # API 公共响应
│   │   ├── spaces.py              # 学习空间请求与响应
│   │   └── quizzes.py             # 测验请求与响应
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── space_service.py
│   │   ├── analysis_orchestrator.py
│   │   ├── source_preprocessor.py
│   │   ├── plan_service.py
│   │   └── quiz_service.py
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── content/
│   │   │   ├── __init__.py
│   │   │   ├── demo.py
│   │   │   ├── zhihu.py
│   │   │   └── fallback.py
│   │   └── llm/
│   │       ├── __init__.py
│   │       ├── openai_compatible.py
│   │       └── json_parser.py
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── supabase_repository.py
│   │   └── memory_repository.py   # 测试与无数据库开发
│   │
│   └── prompts/
│       ├── extract_viewpoint_v1.txt
│       ├── synthesize_v1.txt
│       ├── create_plan_v1.txt
│       ├── create_quiz_v1.txt
│       └── grade_quiz_v1.txt
│
├── data/
│   ├── demo_sources.json
│   ├── demo_analysis.json
│   └── demo_plan.json
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── zhihu_search_response.json
│   │   ├── llm_extract_response.json
│   │   └── llm_synthesis_response.json
│   ├── unit/
│   │   ├── test_source_preprocessor.py
│   │   ├── test_analysis_validation.py
│   │   └── test_json_parser.py
│   ├── contract/
│   │   ├── test_demo_provider_contract.py
│   │   └── test_zhihu_provider_contract.py
│   └── integration/
│       └── test_analysis_flow.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### 2.1 每个目录解决什么问题

| 目录 | 只允许放什么 | 不允许放什么 |
|---|---|---|
| `api` | HTTP 路由、Depends | 模型调用、数据库细节 |
| `core` | 全局配置、日志、错误、中间件 | 具体业务流程 |
| `domain` | 稳定的数据模型和抽象接口 | FastAPI、Supabase SDK |
| `schemas` | 前端请求和响应格式 | 供应商原始格式 |
| `services` | 业务用例和流程编排 | HTTP Header、SQL/SDK 细节 |
| `providers` | 外部内容与模型适配 | 页面响应拼装 |
| `repositories` | 数据持久化 | Prompt 和业务判断 |
| `prompts` | 有版本的纯文本提示词 | Python 业务逻辑 |
| `tests` | 测试与固定样例 | 正式密钥、个人数据 |

---

## 3. 请求从进入到返回的完整路径

以“执行主题分析”为例：

```text
前端 POST /api/spaces/{id}/analyze
  │
  ▼
spaces.py Route
  │ 只校验 client_id 和 force
  ▼
AnalysisOrchestrator.run()
  │
  ├─ SpaceRepository.get_owned_space()
  ├─ SpaceRepository.try_mark_analyzing()
  ├─ ContentProvider.search()
  │    └─ ZhihuProvider 失败 → DemoProvider
  ├─ SourcePreprocessor.normalize_and_rank()
  ├─ SpaceRepository.replace_sources()
  ├─ LLMPort.generate_structured()：逐来源抽取
  ├─ LLMPort.generate_structured()：综合观点与图谱
  ├─ AnalysisResult Pydantic 校验
  ├─ SpaceRepository.save_analysis()
  ├─ SpaceRepository.mark_ready()
  └─ 返回领域对象
  │
  ▼
Route 转换为 AnalysisResponse
  │
  ▼
前端收到稳定 JSON
```

其中任何外部服务失败，都由适配器转换为本项目自己的异常类型。Service 不需要识别 HTTPX 或 Supabase 的原始异常。

---

## 4. 领域模型先行

开始写接口前，先把这些稳定类型定义好。它们是整个后端的“共同语言”。

### 4.1 枚举

`app/domain/enums.py`：

```python
from enum import StrEnum


class UserLevel(StrEnum):
    BEGINNER = "beginner"
    STARTER = "starter"
    EXPERIENCED = "experienced"


class LearningGoal(StrEnum):
    UNDERSTAND = "understand"
    PROJECT = "project"
    INTERVIEW = "interview"


class SpaceStatus(StrEnum):
    CREATED = "created"
    ANALYZING = "analyzing"
    READY = "ready"
    FAILED = "failed"


class SourceProvider(StrEnum):
    ZHIHU = "zhihu"
    DEMO = "demo"


class ConceptCategory(StrEnum):
    CORE = "core"
    PREREQUISITE = "prerequisite"
    PRACTICE = "practice"
    DEBATE = "debate"
    EXTENSION = "extension"


class EdgeType(StrEnum):
    PREREQUISITE_OF = "PREREQUISITE_OF"
    PART_OF = "PART_OF"
    LEARN_AFTER = "LEARN_AFTER"
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    APPLIES_TO = "APPLIES_TO"
```

枚举不能在不同文件中重复写字符串，否则很容易出现 `beginner`、`newbie`、`novice` 三套命名。

### 4.2 内容来源模型

`app/domain/entities.py`：

```python
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl

from app.domain.enums import SourceProvider


class RetrievedSource(BaseModel):
    """Provider 返回、进入业务层前的统一来源格式。"""

    external_id: str
    provider: SourceProvider
    content_type: str = "answer"
    title: str
    author_name: str
    author_badge: str | None = None
    source_url: HttpUrl
    excerpt: str
    published_at: datetime | None = None
    engagement: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


class PreparedSource(RetrievedSource):
    """经过清洗、排序和编号后交给 AI 的来源。"""

    source_key: str


class LearningSpace(BaseModel):
    id: UUID
    client_id: str
    topic: str
    level: str
    goal: str
    daily_minutes: int
    status: str
    error_message: str | None = None
```

为什么要区分 `external_id` 和 `source_key`：

- `external_id` 是知乎或 Demo 数据自己的稳定 ID；
- `source_key` 是当前分析中的 S1、S2；
- 同一篇内容在不同主题里可能被排成不同编号；
- AI 引用只能使用当前分析的 `source_key`。

### 4.3 AI 分析结果模型

`app/domain/analysis_models.py`：

```python
from pydantic import BaseModel, Field, model_validator

from app.domain.enums import ConceptCategory, EdgeType


class Claim(BaseModel):
    text: str = Field(min_length=1, max_length=300)
    evidence: str = Field(min_length=1, max_length=500)
    confidence: float = Field(ge=0, le=1)


class ExtractedConcept(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    definition: str = Field(min_length=1, max_length=300)


class SourceViewpoint(BaseModel):
    source_key: str
    relevance_score: float = Field(ge=0, le=1)
    position_summary: str = Field(min_length=1, max_length=300)
    claims: list[Claim] = Field(default_factory=list, max_length=8)
    concepts: list[ExtractedConcept] = Field(default_factory=list, max_length=12)
    suitable_for: list[str] = Field(default_factory=list, max_length=8)
    limitations: list[str] = Field(default_factory=list, max_length=8)


class ConsensusItem(BaseModel):
    id: str
    title: str
    detail: str
    source_keys: list[str] = Field(min_length=2)


class DebateSide(BaseModel):
    title: str
    reason: str
    suitable_for: list[str]
    source_keys: list[str] = Field(min_length=1)


class DisagreementItem(BaseModel):
    id: str
    question: str
    side_a: DebateSide
    side_b: DebateSide
    how_to_choose: str


class GraphConcept(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]{1,64}$")
    label: str
    category: ConceptCategory
    description: str
    source_keys: list[str] = Field(min_length=1)


class GraphEdge(BaseModel):
    source: str
    target: str
    type: EdgeType
    label: str


class AnalysisResult(BaseModel):
    overview: str
    consensus: list[ConsensusItem]
    disagreements: list[DisagreementItem]
    concepts: list[GraphConcept]
    edges: list[GraphEdge]
    warnings: list[str] = Field(default_factory=list)

    def validate_references(self, valid_source_keys: set[str]) -> None:
        referenced: list[str] = []

        for item in self.consensus:
            referenced.extend(item.source_keys)
        for item in self.disagreements:
            referenced.extend(item.side_a.source_keys)
            referenced.extend(item.side_b.source_keys)
        for item in self.concepts:
            referenced.extend(item.source_keys)

        unknown_sources = set(referenced) - valid_source_keys
        if unknown_sources:
            raise ValueError(f"Unknown source keys: {sorted(unknown_sources)}")

        concept_ids = {item.id for item in self.concepts}
        if len(concept_ids) != len(self.concepts):
            raise ValueError("Concept IDs must be unique")

        for edge in self.edges:
            if edge.source not in concept_ids or edge.target not in concept_ids:
                raise ValueError(
                    f"Edge references unknown concept: {edge.source} -> {edge.target}"
                )
```

注意：Pydantic 校验字段格式，`validate_references()` 校验跨字段关系。二者都必须执行。

---

## 5. 抽象接口：防止将来全盘重写的关键

`app/domain/ports.py` 中一次性定义外部能力。

### 5.1 内容提供器接口

```python
from typing import Protocol, TypeVar
from uuid import UUID
from pydantic import BaseModel

from app.domain.entities import LearningSpace, RetrievedSource, PreparedSource
from app.domain.analysis_models import AnalysisResult, SourceViewpoint


class ContentProviderPort(Protocol):
    async def search(self, query: str, limit: int) -> list[RetrievedSource]: ...
```

业务层只调用 `search()`，不判断数据究竟来自知乎还是 Demo。

### 5.2 大模型接口

```python
ModelT = TypeVar("ModelT", bound=BaseModel)


class LLMPort(Protocol):
    async def generate_structured(
        self,
        *,
        task_name: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
    ) -> ModelT: ...
```

Service 不直接调用 `chat/completions`，也不关心供应商是否支持 `response_format`。

### 5.3 Repository 接口

```python
class LearningRepositoryPort(Protocol):
    async def create_space(self, command: dict) -> LearningSpace: ...

    async def get_owned_space(
        self, space_id: UUID, client_id: str
    ) -> LearningSpace | None: ...

    async def try_mark_analyzing(self, space_id: UUID) -> bool: ...

    async def mark_ready(self, space_id: UUID) -> None: ...

    async def mark_failed(self, space_id: UUID, safe_message: str) -> None: ...

    async def replace_sources(
        self, space_id: UUID, sources: list[PreparedSource]
    ) -> None: ...

    async def save_analysis(
        self,
        space_id: UUID,
        result: AnalysisResult,
        source_viewpoints: list[SourceViewpoint],
        model_name: str,
        prompt_version: str,
    ) -> None: ...

    async def get_complete_space(self, space_id: UUID, client_id: str) -> dict | None: ...

    async def save_plan(self, space_id: UUID, plan: dict) -> dict: ...

    async def save_quiz(self, space_id: UUID, quiz: dict) -> dict: ...

    async def get_quiz(self, quiz_id: UUID) -> dict | None: ...

    async def save_attempt(self, quiz_id: UUID, attempt: dict) -> dict: ...
```

Repository 方法围绕业务动作命名，例如 `mark_ready()`，不要把 SDK 的 `table().select()` 泄漏到 Service。

### 5.4 Prompt 读取接口是否需要抽象

MVP 不需要单独建立 `PromptRepositoryPort`。用一个简单 `PromptLoader` 从固定目录读取，并在应用启动时缓存即可。

---

## 6. 配置一次性设计好

`app/core/config.py`：

```python
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "Zhijing API"
    frontend_origin: str = "http://localhost:5173"

    supabase_url: str = ""
    supabase_service_role_key: str = ""

    llm_base_url: str
    llm_api_key: str
    llm_model: str
    llm_timeout_seconds: float = 45

    content_provider: str = "demo"
    zhihu_access_secret: str = ""
    zhihu_api_base_url: str = "https://developer.zhihu.com/api/v1"

    max_sources: int = Field(default=12, ge=3, le=20)
    max_source_chars: int = Field(default=1200, ge=300, le=5000)
    extract_concurrency: int = Field(default=4, ge=1, le=8)
    use_precomputed_demo: bool = False

    prompt_version: str = "v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

### 6.1 配置原则

- 所有 URL、Key、超时、数量限制和开关都进入 Settings；
- 业务代码里不能到处读取 `os.getenv()`；
- 所有布尔开关只在 `container.py` 或编排入口判断；
- 启动时校验必要配置，尽早失败；
- Demo 模式不应该要求知乎 Key；
- MemoryRepository 模式不应该要求 Supabase Key；
- 不同环境使用不同 `.env`，不要修改代码切环境。

### 6.2 建议增加的环境变量

```dotenv
APP_ENV=development
FRONTEND_ORIGIN=http://localhost:5173

REPOSITORY_BACKEND=supabase
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_TIMEOUT_SECONDS=45

CONTENT_PROVIDER=demo
ZHIHU_ACCESS_SECRET=
ZHIHU_API_BASE_URL=https://developer.zhihu.com/api/v1

MAX_SOURCES=12
MAX_SOURCE_CHARS=1200
EXTRACT_CONCURRENCY=4
USE_PRECOMPUTED_DEMO=false
PROMPT_VERSION=v1
```

---

## 7. 统一异常体系

外部库的异常不允许直接返回给前端。建立本项目自己的错误层级。

`app/core/errors.py`：

```python
class AppError(Exception):
    code = "INTERNAL_ERROR"
    safe_message = "服务暂时不可用，请稍后重试。"
    status_code = 500
    retryable = True

    def __init__(self, detail: str | None = None):
        super().__init__(detail or self.safe_message)
        self.detail = detail


class SpaceNotFoundError(AppError):
    code = "SPACE_NOT_FOUND"
    safe_message = "没有找到这个学习主题。"
    status_code = 404
    retryable = False


class AnalysisInProgressError(AppError):
    code = "ANALYSIS_IN_PROGRESS"
    safe_message = "这个主题正在分析，请不要重复提交。"
    status_code = 409
    retryable = True


class ContentUnavailableError(AppError):
    code = "CONTENT_UNAVAILABLE"
    safe_message = "暂时没有找到足够的学习来源。"
    status_code = 503


class LLMTimeoutError(AppError):
    code = "LLM_TIMEOUT"
    safe_message = "AI 分析超时，请重新尝试。"
    status_code = 504


class LLMInvalidOutputError(AppError):
    code = "LLM_INVALID_JSON"
    safe_message = "AI 返回格式异常，请重新尝试。"
    status_code = 502


class RepositoryError(AppError):
    code = "DATABASE_ERROR"
    safe_message = "保存结果失败，请稍后重试。"
    status_code = 503
```

由全局 exception handler 统一返回：

```json
{
  "error": {
    "code": "LLM_TIMEOUT",
    "message": "AI 分析超时，请重新尝试。",
    "retryable": true,
    "request_id": "..."
  }
}
```

日志中记录原始 detail 和堆栈，前端只收到安全信息。

---

## 8. 数据库访问策略

### 8.1 为什么需要 Repository

如果 Service 中到处出现：

```python
supabase.table("learning_spaces").select("*")...
```

以后数据库字段或产品流程一改，所有 Service 都要改。Repository 将这些变化集中到一个文件。

### 8.2 Supabase Repository 职责

`SupabaseLearningRepository` 负责：

- 将数据库字典转换为领域模型；
- 统一处理空结果；
- 将 SDK 异常转换为 `RepositoryError`；
- 所有查询同时包含 `id` 和 `client_id`；
- 对来源进行幂等写入；
- 保存 AI JSON；
- 控制状态转换。

### 8.3 防止重复分析

状态只允许：

```text
created → analyzing → ready
                    ↘ failed

failed  → analyzing
ready   → analyzing 仅 force=true 时
```

`try_mark_analyzing()` 必须是带条件的更新：只有当前为 `created` 或 `failed` 时才更新成功。若两个请求同时进入，只有一个获得执行权，另一个返回 409。

如果 Supabase SDK 难以判断条件更新影响行数，MVP 至少在 Service 层检查状态并让前端禁用重复点击；赛后再用 PostgreSQL RPC 完成严格原子更新。

### 8.4 多步写入没有事务怎么办

Supabase REST 下跨多个请求不构成数据库事务。MVP 使用“可恢复状态机”：

1. 先标记 `analyzing`；
2. 保存来源；
3. 保存分析；
4. 标记 `ready`；
5. 任一步失败则标记 `failed`；
6. 重试时对来源和分析使用 upsert/replace，不产生重复数据。

这样即使中途失败，也能明确恢复，不会把半成品当成成功结果。

### 8.5 MemoryRepository 的价值

`MemoryLearningRepository` 用 Python 字典实现同一套接口，用于：

- 前两小时内不等 Supabase 就跑通业务；
- 单元测试不访问网络；
- 比赛现场 Supabase 故障时本机演示；
- 验证 Service 没有绑定数据库 SDK。

它不是浪费时间。一个最小实现通常不到 150 行，却能显著降低联调风险。

---

## 9. 内容提供器实现

### 9.1 DemoContentProvider 先做

开发第一版只读取 `data/demo_sources.json`：

```python
class DemoContentProvider:
    def __init__(self, file_path: Path):
        self.file_path = file_path

    async def search(self, query: str, limit: int) -> list[RetrievedSource]:
        payload = json.loads(self.file_path.read_text(encoding="utf-8"))
        items = payload["sources"][:limit]
        return [RetrievedSource.model_validate(item) for item in items]
```

Demo 文件本身也必须通过 `RetrievedSource` 校验，不能因为是静态文件就跳过验证。

### 9.2 ZhihuContentProvider 后做

职责只包含：

- 生成 Bearer 鉴权头；
- 添加秒级 `X-Request-Timestamp`；
- 调用 `zhihu_search`；
- 将真实响应转换成 `RetrievedSource`；
- 处理超时、401、429 和非预期响应；
- 不保存数据库；
- 不调用大模型。

调用骨架：

```python
import time
import httpx


class ZhihuContentProvider:
    def __init__(self, base_url: str, access_secret: str, timeout: float = 20):
        self.base_url = base_url.rstrip("/")
        self.access_secret = access_secret
        self.timeout = timeout

    async def search(self, query: str, limit: int) -> list[RetrievedSource]:
        headers = {
            "Authorization": f"Bearer {self.access_secret}",
            "X-Request-Timestamp": str(int(time.time())),
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/content/zhihu_search",
                params={"Query": query},
                headers=headers,
            )

        response.raise_for_status()
        return self._normalize_payload(response.json(), limit)
```

`_normalize_payload()` 必须根据实际 Access Secret 返回的真实样例开发。不要依据网上旧版非官方接口猜字段。

### 9.3 契约测试

所有 ContentProvider 都必须通过同一组测试：

- 返回 `list[RetrievedSource]`；
- 数量不超过 limit；
- URL 合法；
- `external_id` 不为空；
- 标题、作者、正文不为空；
- 不返回重复 `external_id`；
- 供应商错误转换成本项目异常。

这能保证替换 Provider 时 Service 不需要修改。

### 9.4 降级提供器

用装饰器式适配器封装降级，不要把 `if zhihu failed` 写进每个 Service：

```python
class FallbackContentProvider:
    def __init__(self, primary: ContentProviderPort, fallback: ContentProviderPort):
        self.primary = primary
        self.fallback = fallback

    async def search(self, query: str, limit: int) -> list[RetrievedSource]:
        try:
            items = await self.primary.search(query, limit)
            if len(items) >= 3:
                return items
        except AppError:
            pass

        return await self.fallback.search(query, limit)
```

正式实现时要记录降级日志，但不能记录 Access Secret。

---

## 10. 来源清洗服务

`SourcePreprocessor` 是纯业务逻辑，不能依赖网络和数据库，因此非常容易测试。

### 10.1 固定处理顺序

1. 去掉 URL 或 `external_id` 完全重复的来源；
2. 去掉标题、作者、正文为空的来源；
3. 清除多余空白、不可见字符和 HTML 标签；
4. 正文小于最低长度时丢弃；
5. 正文截断到 `max_source_chars`；
6. 根据相关性、互动和多样性排序；
7. 截取前 `max_sources` 条；
8. 按最终顺序分配 S1、S2……。

### 10.2 不要让互动量决定真伪

点赞数可以作为排序信号，但不能直接转换为内容“可信度”。来源排序建议考虑：

- 与主题的文本相关性；
- 是否提供具体论据；
- 作者认证信息是否与主题相关；
- 内容时效；
- 观点多样性；
- 互动量仅作为辅助信号。

24 小时内可以先实现去重、截断和简单排序，观点多样性由 AI 综合阶段识别。

---

## 11. 大模型适配器

### 11.1 单一职责

`OpenAICompatibleLLM` 只负责：

- 构造 HTTP 请求；
- 设置模型、温度和超时；
- 读取模型文本；
- 从代码块中提取 JSON；
- 用传入的 Pydantic 类型校验；
- 失败时修复一次；
- 将错误转换为 `LLMTimeoutError` 或 `LLMInvalidOutputError`。

它不负责判断什么叫“共识”，那是 Prompt 与领域校验共同负责的。

### 11.2 推荐请求设置

- 抽取任务温度：0～0.2；
- 综合任务温度：0.2～0.4；
- 评分任务温度：0～0.2；
- 超时：30～60 秒；
- 每次请求带内部 `task_name` 进入日志；
- 支持供应商 JSON Mode 时开启；
- 不支持 JSON Mode 时依靠提示词和解析器。

### 11.3 JSON 解析顺序

1. 去掉首尾空白；
2. 如果被 ```json 代码块包裹，提取代码块内部；
3. 找到第一个 `{` 和最后一个 `}`；
4. 使用 `json.loads()`；
5. 使用 `response_model.model_validate()`；
6. 若失败，将原始输出、目标 schema 和简化后的错误发送给模型修复一次；
7. 仍失败则抛出 `LLMInvalidOutputError`。

禁止使用 `eval()` 解析模型输出。

### 11.4 日志中的隐私和长度控制

可以记录：

- task_name；
- 模型名；
- 耗时；
- HTTP 状态；
- 输入字符数；
- 输出字符数；
- 是否发生重试；
- 校验错误类型。

不要记录：

- API Key；
- Authorization Header；
- 完整用户敏感输入；
- 完整来源正文；
- 完整模型响应。

开发排错需要原始响应时，只保存脱敏、截断的前 500 字符，并且比赛提交前关闭。

---

## 12. 分析编排器

`AnalysisOrchestrator` 是后端核心，但它仍然只编排抽象接口。

### 12.1 构造函数依赖

```python
class AnalysisOrchestrator:
    def __init__(
        self,
        repository: LearningRepositoryPort,
        content_provider: ContentProviderPort,
        llm: LLMPort,
        preprocessor: SourcePreprocessor,
        prompt_loader: PromptLoader,
        settings: Settings,
    ):
        self.repository = repository
        self.content_provider = content_provider
        self.llm = llm
        self.preprocessor = preprocessor
        self.prompt_loader = prompt_loader
        self.settings = settings
```

### 12.2 编排伪代码

```python
async def run(
    self,
    *,
    space_id: UUID,
    client_id: str,
    force: bool = False,
) -> AnalysisBundle:
    space = await self.repository.get_owned_space(space_id, client_id)
    if space is None:
        raise SpaceNotFoundError()

    if space.status == "ready" and not force:
        cached = await self.repository.get_complete_space(space_id, client_id)
        return AnalysisBundle.model_validate(cached)

    acquired = await self.repository.try_mark_analyzing(space_id)
    if not acquired:
        raise AnalysisInProgressError()

    try:
        raw_sources = await self.content_provider.search(
            space.topic,
            self.settings.max_sources,
        )
        sources = self.preprocessor.prepare(
            raw_sources,
            max_items=self.settings.max_sources,
            max_chars=self.settings.max_source_chars,
        )
        if len(sources) < 3:
            raise ContentUnavailableError()

        await self.repository.replace_sources(space.id, sources)

        viewpoints = await self._extract_all(space, sources)
        useful_viewpoints = [v for v in viewpoints if v.relevance_score >= 0.4]
        if len(useful_viewpoints) < 3:
            raise ContentUnavailableError()

        result = await self._synthesize(space, useful_viewpoints)
        result.validate_references({s.source_key for s in sources})

        await self.repository.save_analysis(
            space.id,
            result,
            useful_viewpoints,
            model_name=self.settings.llm_model,
            prompt_version=self.settings.prompt_version,
        )
        await self.repository.mark_ready(space.id)

        return AnalysisBundle(space=space, sources=sources, analysis=result)
    except Exception as exc:
        await self.repository.mark_failed(space.id, safe_message_for(exc))
        raise
```

### 12.3 并发抽取但限制数量

8～12 条来源逐条串行会很慢，可以使用 `asyncio.Semaphore` 将并发限制为 3～5：

```python
semaphore = asyncio.Semaphore(self.settings.extract_concurrency)

async def extract_one(source: PreparedSource) -> SourceViewpoint:
    async with semaphore:
        return await self._extract_source(space, source)

results = await asyncio.gather(
    *(extract_one(source) for source in sources),
    return_exceptions=True,
)
```

处理结果时：

- 单条抽取失败不必让全部失败；
- 至少 3 条成功才进入综合；
- 记录失败来源编号；
- 在 `warnings` 中提醒部分来源未被成功分析；
- 429 较多时降低并发，不要继续增加并发。

### 12.4 预计算 Demo 分支放在哪里

只在编排器入口处理：

```text
USE_PRECOMPUTED_DEMO=true
    → FixtureLoader 读取并校验 demo_analysis.json
    → 保存数据库
    → 返回同一种 AnalysisBundle
```

前端和 Route 不应该知道结果是不是预计算的。响应可额外包含 `execution_mode` 供演示调试，但不要改变核心结构。

---

## 13. 学习计划服务

### 13.1 输入必须来自已经保存的分析

`PlanService` 不重新搜索内容，也不重新提取观点。它读取：

- 学习空间的 level、goal、daily_minutes；
- 已验证的 AnalysisResult；
- 当前来源编号。

### 13.2 缓存逻辑

- 已有计划时默认直接返回；
- 只有显式 `force=true` 才重新生成；
- 新结果先校验为恰好 7 天再覆盖；
- 生成失败时保留旧计划。

### 13.3 领域校验

除 Pydantic 字段校验外，检查：

- day 正好为 1～7，不重复；
- 每天 `estimated_minutes <= daily_minutes × 1.1`；
- 所有 concept_id 存在；
- 所有 source_key 存在；
- 每天 activities、output、self_check 不为空；
- 第 7 天包含回顾或综合任务。

模型不满足要求时修复一次，仍失败则加载 Demo 缓存或返回可重试错误。

---

## 14. 测验服务

### 14.1 生成测验

输入：

- 学习空间；
- 可选 concept_id；
- 分析结果；
- 来源摘要。

模型输出：

```json
{
  "concept_id": "overfitting",
  "question": "请用一个生活中的例子解释什么是过拟合。",
  "reference_answer": "……",
  "rubric": [
    {"criterion": "说明记住训练样本", "points": 40},
    {"criterion": "说明对新数据表现下降", "points": 40},
    {"criterion": "例子清晰", "points": 20}
  ],
  "source_keys": ["S1", "S5"]
}
```

保存完整对象，但响应前端时删除 `reference_answer` 和详细评分标准，防止直接泄题。

### 14.2 评分

评分 Service 必须从数据库读取题目和参考答案，不能相信前端回传的参考答案。

检查：

- 答案不能为空；
- 长度设置合理上限；
- 分数为 0～100 整数；
- strengths 和 improvements 最多各 3 条；
- 保存尝试后再返回；
- 模型评分失败时不能伪造高分，可以返回“暂时无法评分”。

---

## 15. API Schema 与 Route 写法

### 15.1 创建学习空间请求

`app/schemas/spaces.py`：

```python
from pydantic import BaseModel, Field, field_validator
from app.domain.enums import LearningGoal, UserLevel


class CreateSpaceRequest(BaseModel):
    client_id: str = Field(min_length=16, max_length=128)
    topic: str = Field(min_length=2, max_length=100)
    level: UserLevel
    goal: LearningGoal
    daily_minutes: int

    @field_validator("topic")
    @classmethod
    def normalize_topic(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2:
            raise ValueError("topic is too short")
        return normalized

    @field_validator("daily_minutes")
    @classmethod
    def validate_minutes(cls, value: int) -> int:
        if value not in {15, 30, 60, 90}:
            raise ValueError("daily_minutes must be 15, 30, 60, or 90")
        return value
```

### 15.2 Route 保持短小

```python
@router.post("/spaces/{space_id}/analyze", response_model=AnalysisResponse)
async def analyze_space(
    space_id: UUID,
    request: AnalyzeSpaceRequest,
    service: AnalysisOrchestrator = Depends(get_analysis_orchestrator),
) -> AnalysisResponse:
    bundle = await service.run(
        space_id=space_id,
        client_id=request.client_id,
        force=request.force,
    )
    return AnalysisResponse.from_domain(bundle)
```

如果 Route 超过约 30～40 行，通常说明业务逻辑放错位置。

### 15.3 身份校验

MVP 使用浏览器生成的 `client_id`，它只用于隔离演示数据，不是真正安全认证。

每个读取、分析、计划和测验请求都必须校验资源属于该 `client_id`。不要仅通过 UUID 直接返回数据。

正式上线时，用 Supabase Auth 的用户 ID 替代 `client_id`，Repository 接口仍保持“按 owner 访问”，因此 Service 不需要重写。

---

## 16. 依赖组装与应用入口

### 16.1 只在 container.py 选择具体实现

```python
def build_container(settings: Settings) -> AppContainer:
    if settings.repository_backend == "memory":
        repository = MemoryLearningRepository()
    else:
        repository = SupabaseLearningRepository(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )

    demo_provider = DemoContentProvider(DATA_DIR / "demo_sources.json")

    if settings.content_provider == "zhihu":
        zhihu_provider = ZhihuContentProvider(
            settings.zhihu_api_base_url,
            settings.zhihu_access_secret,
        )
        content_provider = FallbackContentProvider(
            primary=zhihu_provider,
            fallback=demo_provider,
        )
    else:
        content_provider = demo_provider

    llm = OpenAICompatibleLLM(...)

    return AppContainer(
        repository=repository,
        content_provider=content_provider,
        llm=llm,
        ...,
    )
```

除 `container.py` 外，不应再出现 `if provider == "zhihu"` 或 `if database == "supabase"`。

### 16.2 main.py 只做应用初始化

`main.py` 负责：

- 创建 FastAPI；
- 注册 CORS；
- 注册 request_id 中间件；
- 注册全局异常处理器；
- 注册 routes；
- 在 lifespan 中创建和关闭共享 HTTP Client；
- 不写具体业务逻辑。

---

## 17. 日志与可观察性

24 小时项目也需要最小可观察性，否则现场失败时无法判断问题在哪。

### 17.1 每个请求记录

- request_id；
- method；
- path；
- status_code；
- duration_ms；
- space_id（如有）；
- execution_mode：live / demo / precomputed；
- error_code（如有）。

### 17.2 每个 AI 调用记录

- request_id；
- task_name；
- model；
- duration_ms；
- input_chars；
- output_chars；
- retry_count；
- validation_success。

### 17.3 每个内容搜索记录

- provider；
- query_length，不记录完整敏感查询；
- returned_count；
- duration_ms；
- fallback_used。

### 17.4 请求 ID

如果前端传入 `X-Request-ID`，后端沿用；否则生成 UUID。响应头也返回相同 ID。用户报错时只需要提供这个 ID，就能在日志定位。

---

## 18. 缓存与三级降级

后端必须明确区分三种运行模式：

### Level 1：实时正式模式

```text
知乎官方 API → 实时 LLM → Supabase
```

### Level 2：Demo 内容模式

```text
本地 Demo 来源 → 实时 LLM → Supabase 或 MemoryRepository
```

### Level 3：完全预计算模式

```text
本地 Demo 来源 + demo_analysis.json + demo_plan.json
```

### 18.1 切换原则

- 内容搜索失败可以自动从 Level 1 降为 Level 2；
- 模型失败不要对任意用户主题返回不相关缓存；
- 只有用户主题与固定 Demo 主题匹配时才能进入 Level 3；
- 响应中可包含 `execution_mode`，便于团队确认现场状态；
- 对普通用户不需要强调“故障”，可以写“当前使用演示知识集”。

### 18.2 缓存键

如果实现结果缓存，建议使用：

```text
normalized_topic + level + goal + daily_minutes + prompt_version + model_name
```

Prompt 或模型变化后不能误用旧缓存，因此必须包含版本。

---

## 19. 测试架构

### 19.1 测试金字塔

优先顺序：

1. 纯函数单元测试；
2. Provider 契约测试；
3. 使用 MemoryRepository + FakeLLM 的业务集成测试；
4. 少量真实 API 冒烟测试；
5. 不要让自动测试大量消耗模型额度。

### 19.2 必写单元测试

`SourcePreprocessor`：

- 去重；
- 截断；
- 空内容过滤；
- S1～Sn 编号稳定；
- 数量上限。

`AnalysisResult`：

- 引用了不存在的 S99 时失败；
- 重复 concept_id 时失败；
- edge 指向不存在节点时失败；
- 共识只有一个来源时失败。

`JSONParser`：

- 纯 JSON；
- ```json 代码块；
- 前后带解释文字；
- 非法 JSON；
- JSON 合法但字段不合法。

### 19.3 FakeLLM

测试不能依赖真实模型。实现：

```python
class FakeLLM:
    def __init__(self, responses: dict[str, BaseModel]):
        self.responses = responses

    async def generate_structured(self, *, task_name: str, **kwargs):
        return self.responses[task_name]
```

这能稳定测试完整分析流程，并验证 Service 只依赖 `LLMPort`。

### 19.4 Provider 契约测试复用

编写一套公共断言，对 DemoProvider 和 ZhihuProvider 分别执行。真实知乎测试通过保存的脱敏响应 fixture 完成，不在每次测试中访问网络。

### 19.5 最小集成测试

使用：

- `MemoryLearningRepository`；
- `DemoContentProvider`；
- `FakeLLM`；
- FastAPI TestClient 或 HTTPX ASGITransport。

验证：

1. 创建空间；
2. 执行分析；
3. 查询完整结果；
4. 生成计划；
5. 生成测验；
6. 提交答案；
7. 重复分析不会重复生成。

---

## 20. 后端实际开发顺序

不要按“先数据库、再知乎、再模型”的顺序做，因为任何外部服务都可能阻塞。应按由内向外的顺序。

### 阶段 1：架构骨架与契约，约 60～90 分钟

创建：

- [ ] 完整目录；
- [ ] `enums.py`；
- [ ] `entities.py`；
- [ ] `analysis_models.py`；
- [ ] `ports.py`；
- [ ] API schemas；
- [ ] 错误类型；
- [ ] Settings；
- [ ] 空 Route 和 `/health`；
- [ ] `main.py`。

验收：

- 应用能启动；
- `/docs` 能看到计划中的接口；
- `/health` 返回 200；
- 所有模块可以 import；
- 还没有任何真实外部依赖也没关系。

### 阶段 2：内存仓库 + Demo Provider，约 60 分钟

- [ ] `MemoryLearningRepository`；
- [ ] `DemoContentProvider`；
- [ ] `SourcePreprocessor`；
- [ ] 创建学习空间接口；
- [ ] 查询空间接口；
- [ ] 单元测试。

验收：

- 不配置 Supabase、不配置知乎，仍可创建空间并读取 8～12 条 Demo 来源；
- 来源统一为 `RetrievedSource`；
- 重复项被删除；
- S1 编号稳定。

### 阶段 3：FakeLLM 跑通完整业务，约 60～90 分钟

- [ ] `AnalysisOrchestrator`；
- [ ] `FakeLLM`；
- [ ] 分析 API；
- [ ] 缓存读取；
- [ ] 状态转换；
- [ ] 错误处理。

验收：

- 从创建空间到拿到完整分析 JSON 全程成功；
- 第二次访问直接返回缓存；
- 分析失败后状态为 failed；
- 重复提交返回 409 或旧结果。

这一步完成后，架构主干已经闭合，后面只是替换适配器。

### 阶段 4：真实 LLM，约 2～3 小时

- [ ] OpenAI-compatible 调用；
- [ ] PromptLoader；
- [ ] 五份版本化 Prompt；
- [ ] JSONParser；
- [ ] 修复重试；
- [ ] 并发抽取；
- [ ] 综合校验；
- [ ] 保存成功响应 fixture。

验收：

- Demo 来源能得到真实模型分析；
- 共识至少两个来源；
- 来源编号没有编造；
- 图谱所有边合法；
- 模型输出非法时能自动修复或返回安全错误。

### 阶段 5：Supabase Repository，约 90 分钟

- [ ] 执行配套文档中的 SQL；
- [ ] 实现 Repository 接口；
- [ ] 数据库异常转换；
- [ ] 状态更新；
- [ ] 来源 replace/upsert；
- [ ] 保存分析 JSON；
- [ ] 刷新恢复结果。

验收：

- 把 `REPOSITORY_BACKEND` 从 memory 改为 supabase 后，Service 和 Route 不改代码；
- 重启后仍能读取分析结果；
- client_id 不匹配时不能读取。

### 阶段 6：计划与测验，约 2 小时

- [ ] `PlanService`；
- [ ] 7 天校验；
- [ ] `QuizService`；
- [ ] 参考答案不发送前端；
- [ ] 评分结果保存；
- [ ] FakeLLM 和真实 LLM 测试。

验收：

- 计划恰好 7 天；
- 时间不超预算；
- 测验可以生成、提交和评分；
- 刷新后记录仍存在。

### 阶段 7：知乎真实 Provider，最多 90 分钟

仅在已有 Access Secret 时开始：

- [ ] 调通官方请求；
- [ ] 保存脱敏响应 fixture；
- [ ] 完成 normalize；
- [ ] 通过 ContentProvider 契约测试；
- [ ] 失败自动进入 Demo Provider。

超过 90 分钟仍不通，立即停止，使用 Demo Provider。它不应阻塞核心后端。

### 阶段 8：联调、压错和冻结，至少 2 小时

- [ ] CORS；
- [ ] 前端真实请求；
- [ ] 网络超时；
- [ ] 429；
- [ ] 非法模型 JSON；
- [ ] 数据库失败；
- [ ] 模型失败时预计算结果；
- [ ] 结构化日志；
- [ ] README 启动说明；
- [ ] 最终冒烟测试。

---

## 21. 建议时间表：后端负责人 12 小时核心路线

| 时间 | 交付物 | 失败时怎么处理 |
|---|---|---|
| 0:00～1:30 | 完整目录、领域契约、配置、错误、空 API | 不做真实服务 |
| 1:30～2:30 | MemoryRepository、DemoProvider | 直接用固定 JSON |
| 2:30～4:00 | FakeLLM 跑通完整分析用例 | 返回固定合法模型对象 |
| 4:00～6:30 | 真实 LLM、Prompt、JSON 校验与重试 | 使用预计算分析 |
| 6:30～8:00 | Supabase Repository | 继续 MemoryRepository 演示 |
| 8:00～10:00 | 学习计划、测验、评分 | 使用缓存计划和固定测验 |
| 10:00～11:00 | 可选知乎 API | 超时立即切 Demo |
| 11:00～12:00 | 联调、错误场景、冻结 | 只修 P0 阻断问题 |

后续时间留给前后端联调和路演。不要把 20 小时全部用于写后端。

---

## 22. 与前端的协作契约

后端第一小时就把以下内容给前端：

- OpenAPI `/docs` 地址；
- `CreateSpaceRequest` 示例；
- 完整 `AnalysisResponse` mock JSON；
- 错误响应结构；
- 枚举值；
- 哪些请求可能需要 60 秒；
- `execution_mode` 含义。

一旦确认，除非修复严重错误，不随意改字段名。需要增加字段时优先新增可选字段，不删除旧字段。

### 22.1 推荐响应公共字段

```json
{
  "data": {},
  "meta": {
    "request_id": "...",
    "execution_mode": "demo",
    "prompt_version": "v1"
  }
}
```

错误统一使用：

```json
{
  "error": {
    "code": "...",
    "message": "...",
    "retryable": true,
    "request_id": "..."
  }
}
```

如果配套总文档已经约定不使用 `data` 包裹，应在第一小时由前后端确定一种，之后不再改变。关键不是选择哪种，而是全项目一致。

---

## 23. 代码质量红线

出现以下情况必须当场调整，不要继续在错误结构上增加功能：

- Route 直接调用 HTTPX、模型或 Supabase；
- Service 里出现知乎响应字段；
- Service 里出现 `supabase.table()`；
- Provider 直接保存数据库；
- Prompt 以几百行字符串散落在 Python 文件；
- 使用裸 `dict` 贯穿整个业务流程而不校验；
- 模型输出不经 Pydantic 就入库；
- 前端提交参考答案让后端评分；
- 把 Service Role Key 返回给前端；
- 使用 `except Exception: pass` 静默吞错；
- 无限重试外部 API；
- 一个文件同时包含 Route、数据库、Prompt 和模型调用；
- 为赶进度复制两套几乎一样的逻辑。

### 23.1 可以接受的技术债

24 小时内可以接受：

- MemoryRepository 数据重启后丢失；
- 不使用数据库事务；
- 不做向量检索；
- 不做真实用户登录；
- 使用简单图谱布局；
- Demo 主题使用预计算结果；
- 日志先输出 JSON 到标准输出；
- 只支持一个模型接口协议。

这些限制都被稳定接口包裹，赛后可以局部替换，不需要推倒架构。

---

## 24. 开发时的提交顺序

建议按小步提交，任何时间都能回到可运行状态：

1. `chore: scaffold backend layers and settings`
2. `feat: define domain models and ports`
3. `feat: add memory repository and demo content provider`
4. `feat: add space API and unified error responses`
5. `feat: add fake LLM analysis flow`
6. `feat: integrate structured LLM output`
7. `feat: persist learning spaces in Supabase`
8. `feat: generate seven-day learning plans`
9. `feat: add quiz generation and grading`
10. `feat: add Zhihu provider with demo fallback`
11. `test: cover core analysis and failure flows`
12. `docs: finalize backend runbook`

不要一次提交全部代码。出现问题时，小提交能迅速定位和回退。

---

## 25. 本地启动流程

以下命令以 Windows PowerShell 为例。

### 25.1 创建虚拟环境

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 25.2 安装依赖

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 25.3 创建配置

```powershell
Copy-Item .env.example .env
```

先用以下最低风险模式：

```dotenv
REPOSITORY_BACKEND=memory
CONTENT_PROVIDER=demo
USE_PRECOMPUTED_DEMO=false
```

### 25.4 启动

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开：

- 健康检查：<http://127.0.0.1:8000/health>
- API 文档：<http://127.0.0.1:8000/docs>

### 25.5 测试

```powershell
pytest -q
```

测试不应该要求真实知乎 Key，也不应该大量调用真实模型。

---

## 26. 上线前配置矩阵

| 场景 | Repository | Content Provider | AI |
|---|---|---|---|
| 本地写业务 | memory | demo | fake 或真实 |
| 自动测试 | memory | demo fixture | fake |
| 前后端联调 | supabase | demo | 真实 |
| 正式演示优先 | supabase | zhihu + demo fallback | 真实 + cache |
| 断网兜底 | memory 或本地已有数据 | demo | precomputed |

每次切换只修改环境变量或 `container.py` 的组装，不修改 Route 和 Service。

---

## 27. 后端完成定义

### 架构

- [ ] Route 没有外部服务细节；
- [ ] Service 只依赖 Port；
- [ ] Demo/Zhihu 实现同一 ContentProviderPort；
- [ ] Memory/Supabase 实现同一 RepositoryPort；
- [ ] Fake/真实模型实现同一 LLMPort；
- [ ] 所有具体实现只在 container.py 组装。

### 核心功能

- [ ] 创建空间；
- [ ] 执行分析；
- [ ] 查询完整结果；
- [ ] 共识和分歧引用合法；
- [ ] 图谱关系合法；
- [ ] 生成恰好 7 天计划；
- [ ] 生成和评分一道测验；
- [ ] 刷新后恢复数据。

### 稳定性

- [ ] 防止重复分析；
- [ ] 外部调用有超时；
- [ ] 重试次数有限；
- [ ] 内容不足时有安全错误；
- [ ] 知乎失败时切 Demo；
- [ ] 模型失败时固定主题可读取预计算结果；
- [ ] 错误响应包含 request_id；
- [ ] 日志不包含密钥。

### 测试

- [ ] 来源清洗测试；
- [ ] AI JSON 解析测试；
- [ ] 引用一致性测试；
- [ ] Provider 契约测试；
- [ ] 完整业务集成测试；
- [ ] 一次真实部署冒烟测试。

### 安全

- [ ] Service Role Key 只在后端；
- [ ] `.env` 已加入 `.gitignore`；
- [ ] 读取资源时校验 client_id；
- [ ] 参考答案不发前端；
- [ ] 不保存无必要的全文和敏感数据；
- [ ] 不向用户返回底层异常堆栈。

---

## 28. 最终执行原则

如果你只记住五句话：

1. **第一小时先固定领域模型和 Port，不先写外部 API。**
2. **先用 MemoryRepository、DemoProvider 和 FakeLLM 跑通完整闭环。**
3. **知乎、模型和 Supabase 都是可替换适配器，不是业务核心。**
4. **所有外部输入和 AI 输出必须先归一化并通过 Pydantic。**
5. **在能稳定演示后再接真实知乎 API，不能让它阻塞主流程。**

按这个顺序开发，后端主干在前三到四小时就能闭合。后续增加真实服务是在稳定结构上替换适配器，而不是重新组织代码。
