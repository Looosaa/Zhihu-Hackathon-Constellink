# 知径前端

React + TypeScript + Vite 前端。开发环境通过 Vite 将 `/api` 和 `/health` 转发到 `http://127.0.0.1:8000`。

## 启动

请先启动后端，再执行：

```powershell
npm install
npm run dev
```

访问 <http://127.0.0.1:5173>。

## 配置

一般不需要创建 `frontend/.env`。如果前后端部署在不同域名，复制 `.env.example` 为 `.env`，再设置：

```dotenv
VITE_API_BASE_URL=https://你的后端域名
```

不要把 Supabase Service Role Key、大模型 API Key、知乎 AppKey 或 Access Secret 放进任何 `VITE_` 变量，因为这些变量会公开到浏览器。

## 检查

```powershell
npm run lint
npm run build
```
