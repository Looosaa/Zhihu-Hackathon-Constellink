# 知径后端

基于 FastAPI 的分层后端，实现内容检索、多观点分析、知识图谱、7 天学习计划和互动测验。

## 默认运行模式

项目默认使用：

- MemoryRepository：不需要数据库；
- DemoContentProvider：读取本地合成演示来源；
- FakeLLM：离线生成稳定结构化结果。

因此第一次启动不需要任何密钥。默认模式适合前后端联调和比赛兜底，不代表正式内容。

## 快速启动（Windows PowerShell）

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开：

- 健康检查：<http://127.0.0.1:8000/health>
- 交互式接口文档：<http://127.0.0.1:8000/docs>

运行测试：

```powershell
pytest -q
```

## 完整接口流程

1. `POST /api/spaces` 创建学习空间；
2. `POST /api/spaces/{id}/analyze` 执行多观点分析；
3. `GET /api/spaces/{id}?client_id=...` 恢复完整结果；
4. `POST /api/spaces/{id}/plan` 生成 7 天计划；
5. `POST /api/spaces/{id}/quizzes` 生成测验；
6. `POST /api/quizzes/{id}/attempts` 提交答案并评分。

请求示例可以直接在 `/docs` 页面执行。

## 切换真实大模型

编辑 `.env`：

```dotenv
LLM_BACKEND=openai_compatible
LLM_BASE_URL=https://YOUR_PROVIDER/v1
LLM_API_KEY=replace_me
LLM_MODEL=replace_me
LLM_JSON_MODE=true
```

如果供应商不支持 JSON Mode，将 `LLM_JSON_MODE` 设为 `false`。所有模型输出仍会经过 Pydantic 校验，并在格式失败时修复一次。

## 切换 Supabase

1. 在 Supabase SQL Editor 执行 `supabase/schema.sql`；
2. 编辑 `.env`：

```dotenv
REPOSITORY_BACKEND=supabase
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_SERVICE_ROLE_KEY=replace_me
```

Service Role Key 只能存在后端，禁止发送给前端或提交到仓库。

## 切换知乎官方数据开放平台

拿到官方 Access Secret 后编辑：

```dotenv
CONTENT_PROVIDER=zhihu
ZHIHU_ACCESS_SECRET=replace_me
```

知乎 Provider 失败或返回来源不足时会自动切换 Demo Provider。拿到真实接口响应后，应先保存一份脱敏 fixture，并在 `app/providers/content/zhihu.py` 中根据真实字段确认归一化映射。

## 接入知乎 OAuth 登录

先在知乎开放平台登记完整回调地址，再编辑后端 `.env`：

```dotenv
ZHIHU_OAUTH_APP_ID=618
ZHIHU_OAUTH_APP_KEY=replace_me
ZHIHU_OAUTH_REDIRECT_URI=http://127.0.0.1:8000/api/auth/zhihu/callback
ZHIHU_OAUTH_ALLOW_MISSING_STATE=true
OAUTH_COOKIE_SECURE=false
FRONTEND_ORIGIN=http://127.0.0.1:5173
```

本地 HTTP 开发才允许使用 `OAUTH_COOKIE_SECURE=false` 和缺失 `state` 的兼容开关；部署到 HTTPS 后必须分别改为 `true` 和 `false`。回调地址必须与知乎后台登记值逐字一致。OAuth AppKey 和用户令牌只能保存在后端。

## 比赛兜底

完全预计算模式：

```dotenv
REPOSITORY_BACKEND=memory
CONTENT_PROVIDER=demo
LLM_BACKEND=fake
USE_PRECOMPUTED_DEMO=true
```

`data/demo_sources.json` 是合成联调数据，上线或参赛展示前必须替换为有权使用、作者和链接可追溯的真实来源。
