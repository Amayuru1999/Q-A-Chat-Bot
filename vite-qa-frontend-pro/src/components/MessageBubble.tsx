
import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Message } from '@/types'
export default function MessageBubble({ m }: { m: Message }) {
  return (
    <div className={`msg ${m.role}`}>
      {m.role === 'assistant'
        ? <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.content}</ReactMarkdown>
        : m.content}
    </div>
  )
}
