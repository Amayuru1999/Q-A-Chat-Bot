
import React from 'react'
import type { Source } from '@/types'
export default function SourceList({ sources }: { sources: Source[] | undefined }){
  if (!sources || !sources.length) return <div className="empty">No sources yet.</div>
  return (
    <div style={{display:'grid', gap:10}}>
      {sources.map((s, i)=>(
        <div key={i} className="panel" style={{padding:12}}>
          <div style={{fontWeight:700, marginBottom:6}}>
            {s.url ? <a href={s.url} target="_blank" rel="noreferrer">{s.title || s.url}</a> : (s.title || 'Source')}
          </div>
          {s.chunk && <div style={{color:'#98a2b3', whiteSpace:'pre-wrap'}}>{s.chunk}</div>}
          {typeof s.score === 'number' && <div style={{color:'#98a2b3'}}>score: {s.score.toFixed(3)}</div>}
        </div>
      ))}
    </div>
  )
}
