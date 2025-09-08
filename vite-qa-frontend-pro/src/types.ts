
export type Role = 'user' | 'assistant'
export interface Message { id: string; role: Role; content: string }
export interface Source { title?: string; url?: string; chunk?: string; score?: number }
export interface AskRequest { question: string; history?: Message[]; top_k?: number; temperature?: number }
export interface AskResponse { answer: string; sources?: Source[] }
