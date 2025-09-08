
import type { AskRequest, AskResponse } from '@/types'
const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
async function http<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
    ...opts
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json() as Promise<T>
}
export async function ask(body: AskRequest): Promise<AskResponse> {
  return http('/api/ask', { method: 'POST', body: JSON.stringify(body) })
}
export async function upload(file: File): Promise<{ ok: boolean; detail?: string }> {
  const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(`${BASE}/api/upload`, { method: 'POST', body: form as any })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}: ${await res.text()}`)
  return res.json()
}