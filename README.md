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

知乎 OAuth 只有在以下配置都完整时才会开放登录按钮：

```dotenv
ZHIHU_OAUTH_APP_ID=618
ZHIHU_OAUTH_APP_KEY=请填写真实密钥
ZHIHU_OAUTH_REDIRECT_URI=http://127.0.0.1:8000/api/auth/zhihu/callback
ZHIHU_OAUTH_ALLOW_MISSING_STATE=true
OAUTH_COOKIE_SECURE=false
FRONTEND_ORIGIN=http://127.0.0.1:5173
```

`ZHIHU_OAUTH_REDIRECT_URI` 必须与知乎开放平台后台登记的完整回调地址逐字一致。`ZHIHU_OAUTH_ALLOW_MISSING_STATE=true` 只用于兼容本地黑客松联调；生产环境必须关闭，并向平台确认标准 `state` 支持。`AppKey`、Supabase Service Role Key、大模型 API Key 都不能出现在前端源码、URL 或 Git 提交中。

## 提交前检查

```powershell
cd frontend
npm run lint
npm run build

cd ..\backend
.\.venv\Scripts\python.exe -m pytest -q
```

后端的更详细说明见 [backend/README.md](backend/README.md)。
