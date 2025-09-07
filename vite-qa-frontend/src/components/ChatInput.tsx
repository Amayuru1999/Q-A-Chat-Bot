import React, { useState } from 'react'

export default function ChatInput({ disabled, onSend }: { disabled?: boolean, onSend: (text: string) => void }) {
  const [text, setText] = useState('')

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    const q = text.trim()
    if (!q) return
    onSend(q)
    setText('')
  }

  return (
    <form className="inputbar" onSubmit={submit}>
      <input
        type="text"
        placeholder="Ask a question about your documents…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
      />
      <button className="btn primary" disabled={disabled} type="submit">Ask</button>
    </form>
  )
}
