import axios from 'axios'
import type { Document, Session, QAMessage, QuickQuestion, ContentBlock } from '@/types'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

export async function uploadDocument(file: File): Promise<{ id: string; filename: string }> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await api.post('/documents/upload', formData)
  return response.data
}

export async function getDocuments(): Promise<Document[]> {
  const response = await api.get('/documents/')
  return response.data
}

export async function getDocument(id: string): Promise<Document> {
  const response = await api.get(`/documents/${id}`)
  return response.data
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`)
}

export function parseDocument(id: string, onProgress: (data: any) => void): Promise<{
  blocks: ContentBlock[]
  raw_markdown: string
  total_pages: number
}> {
  return new Promise((resolve, reject) => {
    const eventSource = new EventSource(`/api/documents/${id}/parse`)
    
    let blocks: ContentBlock[] = []
    let raw_markdown = ''
    let total_pages = 0
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      onProgress(data)
      
      if (data.type === 'done') {
        blocks = data.blocks || []
        raw_markdown = data.raw_markdown || ''
        total_pages = data.total_pages || 0
        eventSource.close()
        resolve({ blocks, raw_markdown, total_pages })
      } else if (data.type === 'error') {
        eventSource.close()
        reject(new Error(data.error))
      }
    }
    
    eventSource.onerror = (error) => {
      eventSource.close()
      reject(error)
    }
  })
}

export async function createSession(documentId: string): Promise<Session> {
  const response = await api.post('/sessions/', { document_id: documentId })
  return response.data
}

export async function getSession(id: string): Promise<Session> {
  const response = await api.get(`/sessions/${id}`)
  return response.data
}

export async function archiveSession(id: string): Promise<Session> {
  const response = await api.put(`/sessions/${id}/archive`)
  return response.data
}

export async function getSessions(status?: string): Promise<Session[]> {
  const url = status ? `/sessions/?status=${status}` : '/sessions/'
  const response = await api.get(url)
  return response.data.sessions
}

export function askQuestion(
  sessionId: string,
  question: string,
  selectedText: string,
  blockId?: string,
  onChunk: (chunk: any) => void
): Promise<void> {
  return new Promise((resolve, reject) => {
    const eventSource = new EventSource(`/api/qa/ask?session_id=${sessionId}&question=${encodeURIComponent(question)}&selected_text=${encodeURIComponent(selectedText)}&block_id=${blockId || ''}`)
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      onChunk(data)
      
      if (data.type === 'done') {
        eventSource.close()
        resolve()
      } else if (data.type === 'error') {
        eventSource.close()
        reject(new Error(data.error))
      }
    }
    
    eventSource.onerror = (error) => {
      eventSource.close()
      reject(error)
    }
  })
}

export async function getQAHistory(sessionId: string): Promise<QAMessage[]> {
  const response = await api.get(`/qa/history/${sessionId}`)
  return response.data.messages
}

export async function getQuickQuestions(): Promise<QuickQuestion[]> {
  const response = await api.get('/qa/quick-questions')
  return response.data.questions
}

export async function healthCheck(): Promise<{ status: string }> {
  const response = await api.get('/health')
  return response.data
}