import React, { useMemo, useRef, useState } from 'react'
  import { ask } from '@/lib/api'
  import type { Message, AskResponse } from '@/types'
  import MessageBubble from '@/components/MessageBubble'
  import SourceCard from '@/components/SourceCard'
  import ChatInput from '@/components/ChatInput'
  import RightPanel from '@/components/RightPanel'

  export default function App(){
    const [messages, setMessages] = useState<Message[]>([
      { id: crypto.randomUUID(), role: 'assistant', content: 'Hi! I can answer questions about your uploaded documents. Start by asking a question or upload a PDF on the right.' }
    ])
    const [loading, setLoading] = useState(false)
    const [sources, setSources] = useState<AskResponse['sources']>([])
    const [topK, setTopK] = useState(5)
    const [temperature, setTemperature] = useState(0.1)
    const listRef = useRef<HTMLDivElement|null>(null)

    const send = async (text: string) => {
      const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: text }
      setMessages((prev)=> [...prev, userMsg])
      setLoading(true)
      try {
        const res = await ask({ question: text, history: messages.slice(-10), top_k: topK, temperature })
        const aMsg: Message = { id: crypto.randomUUID(), role: 'assistant', content: res.answer }
        setMessages((prev)=> [...prev, aMsg])
        setSources(res.sources || [])
      } catch (e:any) {
        setMessages((prev)=> [...prev, { id: crypto.randomUUID(), role: 'assistant', content: `⚠️ ${e.message}` }])
      } finally {
        setLoading(false)
        queueMicrotask(()=> listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' }))
      }
    }

    const canSend = useMemo(()=> !loading, [loading])

    return (
      <div className="container">
        <header>
          <div className="header-inner">
            <div className="logo" aria-hidden />
            <div style={{display:'grid'}}>
              <div className="title">Learning Assistant</div>
              <div className="subtitle">RAG • Vite + React</div>
            </div>
          </div>
        </header>

        <main>
          <section className="panel chat">
            <div ref={listRef} className="messages">
              {messages.map(m => <MessageBubble key={m.id} m={m} />)}
              {loading && <div className="msg assistant">Thinking…</div>}
            </div>
            <div className="sources">
              {sources?.map((s, i)=>(<SourceCard key={i} s={s} />))}
              {!sources?.length && <div className="muted">No sources yet. Ask a question to see retrieved snippets.</div>}
            </div>
            <ChatInput disabled={!canSend} onSend={send} />
          </section>

          <aside className="right">
            <RightPanel topK={topK} setTopK={setTopK} temperature={temperature} setTemperature={setTemperature} />
            <div className="panel card">
              <div style={{fontWeight:700, marginBottom:8}}>Tips</div>
              <ul>
                <li>Adjust Top K to retrieve more/less chunks.</li>
                <li>Temperature controls creativity vs. determinism.</li>
                <li>Use the upload to add new material to your vector store.</li>
              </ul>
              <div className="muted">Endpoints expected:
                <pre style={{whiteSpace:'pre-wrap'}}>
{`GET  /api/health -> { "status": "ok" }
POST /api/ask    -> { "answer": string, "sources": [{title,url,chunk,score}] }
POST /api/upload (multipart/form-data: file)`}
                </pre>
              </div>
            </div>
          </aside>
        </main>

        <footer>
          Built with ❤️ using Vite + React. Point VITE_API_BASE_URL to your FastAPI.
        </footer>
      </div>
    )
  }
