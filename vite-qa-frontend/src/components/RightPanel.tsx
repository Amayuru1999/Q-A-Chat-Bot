import React, { useRef, useState } from 'react'
import { health, upload } from '@/lib/api'

export default function RightPanel({ topK, setTopK, temperature, setTemperature }: {
  topK: number, setTopK: (n:number)=>void,
  temperature: number, setTemperature: (n:number)=>void
}) {
  const [status, setStatus] = useState<string>('')
  const inputRef = useRef<HTMLInputElement|null>(null)
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

  const ping = async () => {
    try {
      const res = await health()
      setStatus(`Backend OK (${res.status}). ${base}`)
    } catch (e:any) {
      setStatus(`Backend unreachable: ${e.message}`)
    }
  }

  const doUpload = async (file: File) => {
    setStatus('Uploading…')
    try {
      const res = await upload(file)
      setStatus(res.ok ? 'Uploaded & indexed ✅' : `Upload response: ${res.detail || 'ok'}`)
    } catch (e:any) {
      setStatus(`Upload failed: ${e.message}`)
    } finally {
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  return (
    <div className="panel card">
      <div style={{fontWeight:700, marginBottom:8}}>Settings</div>
      <div className="field">
        <label className="muted">API base</label>
        <div>{base}</div>
      </div>
      <div className="row">
        <div className="field">
          <label className="muted">Top K</label>
          <input type="number" min={1} max={20} value={topK} onChange={(e)=>setTopK(parseInt(e.target.value||'5'))} />
        </div>
        <div className="field">
          <label className="muted">Temperature</label>
          <input type="number" step="0.1" min={0} max={2} value={temperature} onChange={(e)=>setTemperature(parseFloat(e.target.value||'0'))} />
        </div>
      </div>
      <div className="field">
        <label className="muted">Upload PDFs / docs to index</label>
        <input ref={inputRef} type="file" onChange={(e)=> e.target.files && doUpload(e.target.files[0])} />
      </div>
      <div className="row">
        <button className="btn" onClick={ping}>Ping backend</button>
      </div>
      <div className="muted" style={{marginTop:10, whiteSpace:'pre-wrap'}}>{status}</div>
    </div>
  )
}
