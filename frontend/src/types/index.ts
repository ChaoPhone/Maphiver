export interface ContentBlock {
  id: string
  type: string
  page?: number
  chapter_path: string[]
  content: string
}

export interface Document {
  id: string
  filename: string
  file_path: string
  page_count?: number
  created_at: string
}

export interface Session {
  id: string
  document_id: string
  status: 'draft' | 'archived'
  created_at: string
  updated_at: string
  document?: Document
}

export interface QAMessage {
  id: string
  session_id: string
  question: string
  selected_text: string
  answer: string
  block_id?: string
  created_at: string
}

export interface QuickQuestion {
  type: string
  template: string
}

export interface ParseProgress {
  type: string
  progress?: number
  stage?: string
  block?: ContentBlock
  total_pages?: number
  raw_markdown?: string
  blocks?: ContentBlock[]
  error?: string
}

export interface AnswerChunk {
  type: 'text' | 'done' | 'error'
  content?: string
  error?: string
}