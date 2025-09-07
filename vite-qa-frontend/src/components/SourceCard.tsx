import React from 'react'
import type { Source } from '@/types'

export default function SourceCard({ s }: { s: Source }) {
  return (
    <div className="source-card">
      <div style={{fontWeight:600, marginBottom: 4}}>
        {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.title || s.url}</a> : (s.title || 'Source')}
      </div>
      {s.chunk && <div className="muted" style={{whiteSpace:'pre-wrap'}}>{s.chunk}</div>}
      {typeof s.score === 'number' && <div className="muted">score: {s.score.toFixed(3)}</div>}
    </div>
  )
}
