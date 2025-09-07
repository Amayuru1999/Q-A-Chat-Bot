# Learning Assistant (RAG) – Vite Frontend

A sleek Vite + React + TypeScript UI for your FastAPI RAG backend.

## Quick start

1) Copy `.env.example` to `.env` and set your backend:
```bash
cp .env.example .env
# edit VITE_API_BASE_URL=http://localhost:8000
```

2) Install and run:
```bash
npm install
npm run dev
```

The app expects the backend to expose:
- `GET /api/health` → `{ "status": "ok" }`
- `POST /api/ask` → `{ "answer": string, "sources": [{ title?, url?, chunk?, score? }] }`
- `POST /api/upload` (multipart) → `{ "ok": true }`

## Customizing for your API

Update `src/lib/api.ts` if your paths or schemas differ. The UI passes `question`, `history` (last 10 messages), `top_k`, and `temperature`.
