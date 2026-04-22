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
  name?: string
  status: 'draft' | 'archived'
  is_pinned?: boolean
  is_starred?: boolean
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

export interface Footprint {
  id: string
  session_id: string
  message_id?: string
  action_type: string
  context?: Record<string, any>
  created_at: string
}

export interface KnowledgeCard {
  id: string
  session_id: string
  source_text: string
  annotation?: string
  block_id?: string
  created_at: string
}

export interface DocumentLink {
  id: string
  source_document_id: string
  target_document_id: string
  link_type: string
  context?: string
  target_document?: Document
  created_at: string
}

export interface ExportRequest {
  session_id: string
  format: 'markdown' | 'pdf'
  include_cards: boolean
  include_qa: boolean
}

export interface ExportResponse {
  content: string
  filename: string
  format: string
}