import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Document, Session, ContentBlock, QAMessage } from '@/types'
import * as api from '@/api'

export const useDocumentStore = defineStore('document', () => {
  const documents = ref<Document[]>([])
  const currentDocument = ref<Document | null>(null)
  const blocks = ref<ContentBlock[]>([])
  const rawMarkdown = ref('')
  const parseProgress = ref(0)
  const parseStage = ref('')
  
  // 暂停/继续控制
  const isPaused = ref(false)
  let currentAbort: (() => void) | null = null

  async function fetchDocuments() {
    documents.value = await api.getDocuments()
  }

  async function uploadFile(file: File) {
    const result = await api.uploadDocument(file)
    await fetchDocuments()
    return result
  }

  async function parseDocument(id: string, onProgress?: (data: any) => void) {
    parseProgress.value = 0
    parseStage.value = 'extracting'
    isPaused.value = false

    const { promise, abort } = api.parseDocument(id, (data) => {
      // 即使暂停也继续接收数据，但不触发 onProgress
      if (!isPaused.value && onProgress) {
        onProgress(data)
      }
      if (data.progress) {
        parseProgress.value = data.progress
      }
      if (data.stage) {
        parseStage.value = data.stage
      }
    })

    currentAbort = abort

    const result = await promise

    blocks.value = result.blocks
    rawMarkdown.value = result.raw_markdown
    parseProgress.value = 100
    parseStage.value = 'done'
    currentAbort = null

    return result
  }

  // 暂停格式化显示
  function pauseParsing() {
    isPaused.value = true
  }

  // 继续格式化显示
  function resumeParsing() {
    isPaused.value = false
  }

  // 停止格式化（完全终止）
  function stopParsing() {
    if (currentAbort) {
      currentAbort()
      currentAbort = null
    }
    isPaused.value = false
    parseStage.value = 'stopped'
  }

  async function loadParsedContent(id: string) {
    try {
      const content = await api.getDocumentContent(id)
      rawMarkdown.value = content.raw_markdown
      parseProgress.value = 100
      parseStage.value = 'done'
      return content
    } catch (error) {
      return null
    }
  }
  
  async function deleteDocument(id: string) {
    await api.deleteDocument(id)
    await fetchDocuments()
  }
  
  return {
    documents,
    currentDocument,
    blocks,
    rawMarkdown,
    parseProgress,
    parseStage,
    isPaused,
    fetchDocuments,
    uploadFile,
    parseDocument,
    pauseParsing,
    resumeParsing,
    stopParsing,
    loadParsedContent,
    deleteDocument,
  }
})

export const useSessionStore = defineStore('session', () => {
  const sessions = ref<Session[]>([])
  const currentSession = ref<Session | null>(null)
  const qaMessages = ref<QAMessage[]>([])
  
  async function fetchSessions(status?: string) {
    sessions.value = await api.getSessions(status)
  }
  
  async function createSession(documentId: string) {
    currentSession.value = await api.createSession(documentId)
    await fetchSessions()
    return currentSession.value
  }
  
  async function loadSession(id: string) {
    currentSession.value = await api.getSession(id)
    qaMessages.value = await api.getQAHistory(id)
  }
  
  async function updateSessionName(id: string, name: string) {
    await api.updateSession(id, name)
    await fetchSessions()
  }

  async function pinStarSession(id: string, isPinned?: boolean, isStarred?: boolean) {
    await api.pinStarSession(id, isPinned, isStarred)
    await fetchSessions()
  }
  
  async function deleteSession(id: string) {
    await api.deleteSession(id)
    await fetchSessions()
  }
  
  async function archiveSession(id: string) {
    await api.archiveSession(id)
    await fetchSessions()
  }
  
  async function askQuestion(question: string, selectedText: string, blockId?: string) {
    if (!currentSession.value) return
    
    const tempMsg: QAMessage = {
      id: 'temp-' + Date.now(),
      session_id: currentSession.value.id,
      question,
      selected_text: selectedText,
      answer: '',
      block_id: blockId,
      created_at: new Date().toISOString(),
    }
    qaMessages.value.push(tempMsg)
    
    try {
      await api.askQuestionStream(
        currentSession.value.id,
        question,
        selectedText,
        blockId,
        (chunk) => {
          if (chunk.type === 'text' && chunk.content) {
            tempMsg.answer += chunk.content
          }
        }
      )
      
      qaMessages.value = await api.getQAHistory(currentSession.value.id)
    } catch (error) {
      qaMessages.value = qaMessages.value.filter(m => m.id !== tempMsg.id)
      throw error
    }
  }
  
  async function askQuestionStream(question: string, selectedText: string, onChunk: (chunk: any) => void, blockId?: string) {
    if (!currentSession.value) return
    
    await api.askQuestionStream(
      currentSession.value.id,
      question,
      selectedText,
      blockId,
      onChunk
    )
    
    qaMessages.value = await api.getQAHistory(currentSession.value.id)
  }
  
  return {
    sessions,
    currentSession,
    qaMessages,
    fetchSessions,
    createSession,
    loadSession,
    updateSessionName,
    pinStarSession,
    deleteSession,
    archiveSession,
    askQuestion,
    askQuestionStream,
  }
})