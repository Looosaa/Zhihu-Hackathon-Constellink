# 知径（Zhihu Hackathon）

知径是一套基于知乎知识内容的 AI 学习辅助应用。前端使用 React + TypeScript，后端使用 FastAPI，并已接入 Supabase、OpenAI 兼容大模型接口和知乎开放平台内容接口。

## 项目结构

```text
Zhihu-Hackathon/
├─ frontend/   React 前端，开发端口 5173
└─ backend/    FastAPI 后端，开发端口 8000
```

前端开发服务器会把 `/api` 和 `/health` 自动转发给后端，因此浏览器只需访问 `http://127.0.0.1:5173`，无需在前端保存任何数据库或大模型密钥。

## 第一次启动

打开两个 PowerShell 窗口。

窗口一（后端）：

```powershell
cd D:\ai\_projects\zhihu\Zhihu-Hackathon\backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

窗口二（前端）：

```powershell
cd D:\ai\_projects\zhihu\Zhihu-Hackathon\frontend
npm install
npm run dev
```

打开：

- 应用页面：<http://127.0.0.1:5173>
- 后端接口文档：<http://127.0.0.1:8000/docs>
- 后端健康检查：<http://127.0.0.1:8000/health>

## 本地配置

真正的密钥只放在 `backend/.env`，该文件已被 Git 忽略，不能提交到 GitHub。可提交的配置模板是 `backend/.env.example`。

本地页面可以预览 OAuth 界面，但知乎真实登录必须使用已经登记的公网 HTTPS 回调，
`localhost` 和 `127.0.0.1` 不会开放登录按钮。部署后的关键配置如下：

```dotenv
ZHIHU_OAUTH_APP_ID=618
ZHIHU_OAUTH_APP_KEY=请填写真实密钥
ZHIHU_OAUTH_REDIRECT_URI=https://你的公网域名/auth/callback
ZHIHU_OAUTH_ALLOW_MISSING_STATE=true
OAUTH_COOKIE_SECURE=true
FRONTEND_ORIGIN=https://你的公网域名
```

`ZHIHU_OAUTH_REDIRECT_URI` 必须与知乎开放平台后台登记的完整回调地址逐字一致。
`ZHIHU_OAUTH_ALLOW_MISSING_STATE=true` 仅用于当前黑客松公网演示，正式产品必须关闭并向平台确认标准 `state` 支持。
`AppKey`、Supabase Service Role Key、大模型 API Key 都不能出现在前端源码、URL 或 Git 提交中。

## Render 部署与知乎登录

项目根目录的 `render.yaml` 和 `Dockerfile` 会把 React 与 FastAPI 构建成一个 Render Web Service。
前后端使用同一个域名，Render 提供的 `RENDER_EXTERNAL_URL` 会自动生成前端地址与 OAuth 回调地址。

1. 把当前代码推送到 GitHub。
2. 在 Render 选择 **New → Blueprint**，连接本仓库并读取根目录的 `render.yaml`。
3. 首次创建时，在 Render 的 Secret 输入页填写：`SUPABASE_URL`、`SUPABASE_SERVICE_ROLE_KEY`、`LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL`、`ZHIHU_ACCESS_SECRET`、`ZHIHU_OAUTH_APP_KEY`。
4. 部署成功后复制 Render 公网地址，例如 `https://zhijing-xxx.onrender.com`。
5. 将 `https://zhijing-xxx.onrender.com/auth/callback` 登记为知乎 OAuth 回调地址，必须逐字一致。
6. 重新部署后，在公网页面点击“知乎登录”，最后的知乎授权确认必须由用户本人完成。

当前知乎实测回调可能不返回标准 `state`。项目用 HttpOnly 浏览器关联 Cookie 做了黑客松演示兼容，
界面会明确标记“演示登录”；这不是生产级 OAuth 安全方案，正式上线前需要平台确认标准 `state` 或 PKCE 支持。

## 提交前检查

```powershell
cd frontend
npm run lint
npm run build

cd ..\backend
.\.venv\Scripts\python.exe -m pytest -q
```

后端的更详细说明见 [backend/README.md](backend/README.md)。
