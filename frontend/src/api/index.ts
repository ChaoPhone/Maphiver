import axios from 'axios'
import type { Document, Session, QAMessage, QuickQuestion, ContentBlock, Footprint, KnowledgeCard, DocumentLink, ExportRequest, ExportResponse } from '@/types'

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

export async function getDocumentContent(id: string): Promise<{ id: string; filename: string; raw_markdown: string; parsed_at: string }> {
  const response = await api.get(`/documents/${id}/content`)
  return response.data
}

export async function deleteDocument(id: string): Promise<void> {
  await api.delete(`/documents/${id}`)
}

export function parseDocument(
  id: string,
  onProgress: (data: any) => void
): {
  promise: Promise<{
    blocks: ContentBlock[]
    raw_markdown: string
    total_pages: number
  }>
  abort: () => void
} {
  const controller = new AbortController()

  let blocks: ContentBlock[] = []
  let raw_markdown = ''
  let total_pages = 0
  let lastDataTime = Date.now()

  const promise = new Promise<{
    blocks: ContentBlock[]
    raw_markdown: string
    total_pages: number
  }>(async (resolve, reject) => {
    const stallTimer = setInterval(() => {
      if (Date.now() - lastDataTime > 120000) {
        controller.abort()
        clearInterval(stallTimer)
        reject(new Error('解析超时，请重试'))
      }
    }, 15000)

    try {
      const response = await fetch(`/api/documents/${id}/parse`, {
        signal: controller.signal,
      })

      if (!response.ok) {
        clearInterval(stallTimer)
        reject(new Error(`HTTP error! status: ${response.status}`))
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        clearInterval(stallTimer)
        reject(new Error('No reader available'))
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        lastDataTime = Date.now()
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              onProgress(data)

              if (data.type === 'done') {
                clearInterval(stallTimer)
                blocks = data.blocks || []
                raw_markdown = data.raw_markdown || ''
                total_pages = data.total_pages || 0
                resolve({ blocks, raw_markdown, total_pages })
                return
              }
              if (data.type === 'error') {
                clearInterval(stallTimer)
                reject(new Error(data.error))
                return
              }
            } catch {
              // skip malformed JSON lines
            }
          }
        }
      }

      clearInterval(stallTimer)
      reject(new Error('Stream ended unexpectedly'))
    } catch (error: any) {
      clearInterval(stallTimer)
      if (error.name === 'AbortError') {
        reject(new Error('解析已停止'))
      } else {
        reject(error)
      }
    }
  })

  return { promise, abort: () => controller.abort() }
}

export async function createSession(documentId: string): Promise<Session> {
  const response = await api.post('/sessions/', { document_id: documentId })
  return response.data
}

export async function getSession(id: string): Promise<Session> {
  const response = await api.get(`/sessions/${id}`)
  return response.data
}

export async function updateSession(id: string, name: string): Promise<Session> {
  const response = await api.put(`/sessions/${id}`, { name })
  return response.data
}

export async function pinStarSession(id: string, isPinned?: boolean, isStarred?: boolean): Promise<Session> {
  const response = await api.put(`/sessions/${id}/pin-star`, {
    is_pinned: isPinned,
    is_starred: isStarred,
  })
  return response.data
}

export async function deleteSession(id: string): Promise<void> {
  await api.delete(`/sessions/${id}`)
}

export async function archiveSession(id: string): Promise<Session> {
  const response = await api.put(`/sessions/${id}/archive`)
  return response.data
}

export async function getSessions(status?: string): Promise<Session[]> {
  const url = status ? `/sessions/?status=${encodeURIComponent(status)}` : '/sessions/'
  const response = await api.get(url)
  return response.data.sessions
}

export async function askQuestionStream(
  sessionId: string,
  question: string,
  selectedText: string,
  blockId?: string,
  onChunk?: (chunk: any) => void
): Promise<void> {
  const response = await fetch('/api/qa/ask', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      question,
      selected_text: selectedText,
      block_id: blockId || null,
    }),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) {
    throw new Error('No reader available')
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        onChunk(data)
        
        if (data.type === 'done') {
          return
        }
        if (data.type === 'error') {
          throw new Error(data.error)
        }
      }
    }
  }
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

export async function getFootprints(sessionId: string): Promise<Footprint[]> {
  const response = await api.get(`/footprints/${sessionId}`)
  return response.data.footprints
}

export async function createFootprint(
  sessionId: string,
  actionType: string,
  context?: Record<string, any>,
  messageId?: string
): Promise<Footprint> {
  const response = await api.post('/footprints/', {
    session_id: sessionId,
    action_type: actionType,
    context,
    message_id: messageId,
  })
  return response.data
}

export async function getCards(sessionId?: string): Promise<KnowledgeCard[]> {
  const url = sessionId ? `/cards/?session_id=${sessionId}` : '/cards/'
  const response = await api.get(url)
  return response.data.cards
}

export async function getCard(id: string): Promise<KnowledgeCard> {
  const response = await api.get(`/cards/${id}`)
  return response.data
}

export async function createCard(
  sessionId: string,
  sourceText: string,
  annotation?: string,
  blockId?: string
): Promise<KnowledgeCard> {
  const response = await api.post('/cards/', {
    session_id: sessionId,
    source_text: sourceText,
    annotation,
    block_id: blockId,
  })
  return response.data
}

export async function updateCard(id: string, annotation: string): Promise<KnowledgeCard> {
  const response = await api.put(`/cards/${id}`, { annotation })
  return response.data
}

export async function deleteCard(id: string): Promise<void> {
  await api.delete(`/cards/${id}`)
}

export async function getDocumentLinksBySource(documentId: string): Promise<DocumentLink[]> {
  const response = await api.get(`/document-links/source/${documentId}`)
  return response.data.links
}

export async function getDocumentLinksByTarget(documentId: string): Promise<DocumentLink[]> {
  const response = await api.get(`/document-links/target/${documentId}`)
  return response.data.links
}

export async function createDocumentLink(
  sourceDocumentId: string,
  targetDocumentId: string,
  linkType?: string,
  context?: string
): Promise<DocumentLink> {
  const response = await api.post('/document-links/', {
    source_document_id: sourceDocumentId,
    target_document_id: targetDocumentId,
    link_type: linkType || 'reference',
    context,
  })
  return response.data
}

export async function deleteDocumentLink(linkId: string): Promise<void> {
  await api.delete(`/document-links/${linkId}`)
}

export async function exportSession(request: ExportRequest): Promise<ExportResponse> {
  const response = await api.post('/export/', request)
  return response.data
}