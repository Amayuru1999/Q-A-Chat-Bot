export type Role = 'user' | 'assistant' | 'system';
export interface Message {
  id: string;
  role: Role;
  content: string;
}
export interface AskRequest {
  question: string;
  history?: Message[];
  top_k?: number;
  temperature?: number;
}
export interface Source {
  title?: string;
  url?: string;
  chunk?: string;
  score?: number;
}
export interface AskResponse {
  answer: string;
  sources?: Source[];
}
