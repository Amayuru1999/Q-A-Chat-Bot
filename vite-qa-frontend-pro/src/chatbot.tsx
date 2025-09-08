import React, { useMemo, useRef, useState } from 'react'
import type { Message, AskResponse } from '@/types'
import { ask, upload } from '@/lib/api'
import MessageBubble from '@/components/MessageBubble'
import SourceList from '@/components/SourceList'
import Header from './components/Header'

export default function Chatbot(){
  const [messages, setMessages] = useState<Message[]>([
    { id: crypto.randomUUID(), role: 'assistant', content: 'Hi! I can answer questions about your uploaded documents. Upload a PDF/TXT/DOCX and ask a question below.' }
  ])
  const [loading, setLoading] = useState(false)
  const [sources, setSources] = useState<AskResponse['sources']>([])
  const [text, setText] = useState('')
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState<string>('')

  const listRef = useRef<HTMLDivElement|null>(null)
  const fileInputRef = useRef<HTMLInputElement|null>(null)

  const send = async () => {
    const q = text.trim()
    if (!q) return
    setText('')
    setMessages(prev => [...prev, { id: crypto.randomUUID(), role:'user', content:q }])
    setLoading(true)
    try {
      const res = await ask({ question: q, history: messages.slice(-10), top_k: 5, temperature: 0.1 })
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role:'assistant', content: res.answer }])
      setSources(res.sources || [])
    } catch (e:any) {
      setMessages(prev => [...prev, { id: crypto.randomUUID(), role:'assistant', content: `⚠️ ${e.message}` }])
    } finally {
      setLoading(false)
      queueMicrotask(()=> listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' }))
    }
  }

  const handleFiles = async (files: FileList | null) => {
    if (!files || !files.length) return
    setUploading(true)
    setUploadMsg('Uploading & indexing…')
    try {
      const results = await Promise.allSettled(
        Array.from(files).map(f => upload(f))
      )
      const ok = results.filter(r => r.status === 'fulfilled' && (r as any).value?.ok).length
      const total = results.length
      const errs = results
        .filter(r => r.status === 'rejected')
        .map((r:any) => r.reason?.message || 'error')
      setUploadMsg(ok === total
        ? `Uploaded & indexed ${ok}/${total} ✅`
        : `Indexed ${ok}/${total}. ${errs.length ? 'Errors: ' + errs.join(', ') : ''}`)
      // Nudge the user to ask a question now
      setMessages(prev => [...prev, {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: `Your document${total>1?'s':''} ${ok ? 'are' : 'is'} indexed. Ask a question to query them!`
      }])
    } catch (e:any) {
      setUploadMsg(`Upload failed: ${e.message}`)
    } finally {
      setUploading(false)
      setTimeout(()=> setUploadMsg(''), 5000)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const canSend = useMemo(()=> !loading && !uploading, [loading, uploading])

  return (
    <div className="wrap">
      <Header />
     

      <main>
        <section className="panel chat">
          <div
            ref={listRef}
            className="messages"
            onDragOver={(e)=>{ e.preventDefault() }}
            onDrop={(e)=>{ e.preventDefault(); handleFiles(e.dataTransfer.files) }}
            title="Drop files anywhere in the chat to upload"
          >
            {messages.map(m => <MessageBubble key={m.id} m={m} />)}
            {loading && <div className="msg assistant">Thinking…</div>}
          </div>

          <div style={{padding:'0 16px 14px'}}>
            <SourceList sources={sources} />
          </div>

          <form className="composer" onSubmit={(e)=>{e.preventDefault(); send()}}>
            <input
              type="text"
              placeholder="Ask a question about your documents…"
              value={text}
              onChange={(e)=>setText(e.target.value)}
              disabled={!canSend}
            />
            {/* Upload button */}
            <label className="btn" style={{cursor:'pointer'}}>
              Upload
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.txt,.md,.docx"
                style={{ display:'none' }}
                onChange={(e)=> handleFiles(e.target.files)}
              />
            </label>
            <button className="btn primary" disabled={!canSend} type="submit">
              {uploading ? 'Indexing…' : 'Ask'}
            </button>
          </form>

          {uploadMsg && (
            <div style={{padding:'6px 12px 12px', color:'#98a2b3'}}>{uploadMsg}</div>
          )}
        </section>
      </main>

      <footer>Built with  using Vite + React.</footer>
    </div>
  )
}