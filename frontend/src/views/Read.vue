<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore, useDocumentStore } from '@/stores'
import { marked } from 'marked'
import katex from 'katex'
import { ElMessage, ElScrollbar, ElUpload, ElProgress, ElIcon } from 'element-plus'
import { ChatDotRound, UploadFilled, Notebook, EditPen, QuestionFilled, Close, ArrowLeft, Sunny, Moon, FullScreen, Reading } from '@element-plus/icons-vue'
import type { KnowledgeCard } from '@/types'
import * as api from '@/api'
import FootprintPanel from '@/components/FootprintPanel.vue'
import { extractLatexBlocks } from '@/utils/latex'

marked.setOptions({ breaks: true, gfm: true })

const isDarkMode = ref(false)
const isFocusMode = ref(false)

function toggleTheme() {
  isDarkMode.value = !isDarkMode.value
  if (isDarkMode.value) {
    document.documentElement.setAttribute('data-theme', 'dark')
  } else {
    document.documentElement.removeAttribute('data-theme')
  }
  localStorage.setItem('maphiver-theme', isDarkMode.value ? 'dark' : 'light')
}

function toggleFocusMode() {
  isFocusMode.value = !isFocusMode.value
}

onMounted(() => {
  const savedTheme = localStorage.getItem('maphiver-theme')
  if (savedTheme === 'dark') {
    isDarkMode.value = true
    document.documentElement.setAttribute('data-theme', 'dark')
  }
})

function renderMarkdownWithLatex(markdown: string): string {
  if (!markdown) return ''
  
  const { text, blocks } = extractLatexBlocks(markdown)
  
  let result = marked.parse(text, { breaks: true, gfm: true }) as string
  
  blocks.forEach(block => {
    try {
      const rendered = katex.renderToString(block.formula, {
        displayMode: block.display,
        throwOnError: false,
        output: 'html',
        trust: true,
      })
      result = result.replace(block.placeholder, rendered)
    } catch (e) {
      console.warn('KaTeX render error for:', block.formula, e)
      result = result.replace(block.placeholder, block.display ? `$$${block.formula}$$` : `$${block.formula}$`)
    }
  })
  
  return result
}

const route = useRoute()
const router = useRouter()
const sessionStore = useSessionStore()
const documentStore = useDocumentStore()

const loading = ref(false)
const uploading = ref(false)
const parsing = ref(false)
const parseProgress = ref(0)
const parseStage = ref('')
const streamingContent = ref('')
const displayContent = ref('')
let streamBuffer = ''
let displayTimer: number | null = null
const fileList = ref<any[]>([])

const selectedText = ref('')
const selectedRange = ref<{ start: number; end: number; rect: DOMRect | null }>({ start: 0, end: 0, rect: null })
const question = ref('')
const answering = ref(false)
const streamingAnswer = ref('')
const showCurrentPanel = ref(false)
const contentRef = ref<HTMLElement | null>(null)
const scrollContainerRef = ref<HTMLElement | null>(null)
const cards = ref<KnowledgeCard[]>([])
const cardsLoading = ref(false)
const sidebarHovered = ref(false)
const showCardInput = ref(false)
const cardAnnotation = ref('')
const cardCreating = ref(false)
const cardSuccess = ref(false)
const currentChapter = ref('')
const showBreadcrumb = ref(false)
const expandedHistoryId = ref<string | null>(null)
const panelPosition = ref({ top: 0, right: 0 })

const sessionId = computed(() => route.params.sessionId as string)
const hasDocument = computed(() => !!sessionStore.currentSession?.document_id)
const qaMessages = computed(() => sessionStore.qaMessages)
const documentTitle = computed(() => sessionStore.currentSession?.document?.filename || '流式知识河')
const documentPageCount = computed(() => sessionStore.currentSession?.document?.page_count || 0)
const readingSummary = computed(() => {
  const parts: string[] = []
  if (documentPageCount.value) {
    parts.push(`${documentPageCount.value} 页`)
  }
  parts.push(`${qaMessages.value.length} 条问答`)
  parts.push(`${cards.value.length} 张卡片`)
  return parts.join(' · ')
})

const renderedMarkdown = computed(() => {
  return renderMarkdownWithLatex(documentStore.rawMarkdown)
})

const quickQuestions = [
  { type: 'explain', label: '解释', template: '请解释这段内容' },
  { type: 'summary', label: '总结', template: '请总结这段内容的核心要点' },
  { type: 'example', label: '举例', template: '请举例说明这个概念' },
  { type: 'solve', label: '解题', template: '请给出这道题的详细解答步骤' },
]

onMounted(async () => {
  if (sessionId.value) {
    await loadSessionData()
  }
  setupScrollObserver()
})

onUnmounted(() => {
  removeScrollObserver()
  if (displayTimer) {
    clearInterval(displayTimer)
    displayTimer = null
  }
})

let scrollObserver: IntersectionObserver | null = null

function setupScrollObserver() {
  scrollObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const heading = entry.target as HTMLElement
          const text = heading.textContent || ''
          currentChapter.value = text
          showBreadcrumb.value = true
        }
      })
    },
    {
      root: null,
      rootMargin: '-80px 0px -80% 0px',
      threshold: 0,
    }
  )
}

function removeScrollObserver() {
  if (scrollObserver) {
    scrollObserver.disconnect()
    scrollObserver = null
  }
}

function observeHeadings() {
  if (!scrollObserver || !contentRef.value) return
  
  scrollObserver.disconnect()
  
  const headings = contentRef.value.querySelectorAll('h1, h2, h3')
  headings.forEach((heading) => {
    scrollObserver!.observe(heading)
  })
}

watch(renderedMarkdown, () => {
  nextTick(() => {
    observeHeadings()
  })
})

async function loadSessionData() {
  loading.value = true
  try {
    await sessionStore.loadSession(sessionId.value)
    if (sessionStore.currentSession?.document_id) {
      await documentStore.parseDocument(sessionStore.currentSession.document_id)
    }
    await loadCards()
  } catch (error) {
    ElMessage.error('加载失败')
  }
  loading.value = false
}

async function loadCards() {
  if (!sessionId.value) return
  cardsLoading.value = true
  try {
    cards.value = await api.getCards(sessionId.value)
  } catch (error) {
    console.error('加载卡片失败', error)
  }
  cardsLoading.value = false
}

function handleFileChange(uploadFile: any) {
  fileList.value = [uploadFile]
  return false
}

function startCharByCharDisplay() {
  if (displayTimer) {
    clearInterval(displayTimer)
  }
  displayTimer = window.setInterval(() => {
    if (streamBuffer.length > 0) {
      const char = streamBuffer.charAt(0)
      streamBuffer = streamBuffer.slice(1)
      displayContent.value += char
    } else if (!parsing.value) {
      if (displayTimer) {
        clearInterval(displayTimer)
        displayTimer = null
      }
    }
  }, 30)
}

async function handleUpload() {
  if (fileList.value.length === 0 || !fileList.value[0].raw) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  parseProgress.value = 0
  parseStage.value = ''
  streamingContent.value = ''
  displayContent.value = ''
  streamBuffer = ''
  
  try {
    const result = await documentStore.uploadFile(fileList.value[0].raw)
    ElMessage.success('上传成功')
    
    uploading.value = false
    parsing.value = true
    parseStage.value = '提取文本...'
    parseProgress.value = 10
    
    const session = await sessionStore.createSession(result.id)
    router.push(`/read/${session.id}`)
    
    await documentStore.parseDocument(result.id, (data: any) => {
      if (data.type === 'progress') {
        parseStage.value = getStageLabel(data.stage)
        parseProgress.value = data.progress || parseProgress.value
      } else if (data.type === 'text' && data.content) {
        streamBuffer += data.content
        if (!displayTimer) {
          startCharByCharDisplay()
        }
        parseStage.value = 'AI格式化中...'
      }
    })
    
    parseProgress.value = 100
    parseStage.value = '解析完成'
    ElMessage.success('解析完成')
    await loadCards()
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
  uploading.value = false
  parsing.value = false
  fileList.value = []
}

function getStageLabel(stage: string): string {
  const labels: Record<string, string> = {
    'extracting': '提取文本...',
    'extracted': '文本提取完成',
    'formatting': 'AI格式化...',
    'streaming': '流式输出...',
  }
  return labels[stage] || stage
}

function handleTextSelection(event: MouseEvent) {
  const selection = window.getSelection()
  if (selection && selection.toString().trim()) {
    const text = selection.toString().trim()
    if (text.length >= 1) {
      selectedText.value = text
      
      const range = selection.getRangeAt(0)
      const rect = range.getBoundingClientRect()
      selectedRange.value = {
        start: range.startOffset,
        end: range.endOffset,
        rect: rect
      }
      
      const scrollRect = scrollContainerRef.value?.getBoundingClientRect()
      if (scrollRect && rect) {
        const panelHeight = 400
        const panelTop = rect.top - scrollRect.top
        
        let adjustedTop = panelTop
        
        if (adjustedTop < 20) {
          adjustedTop = 20
        } else if (adjustedTop + panelHeight > scrollRect.height - 20) {
          adjustedTop = scrollRect.height - panelHeight - 20
        }
        
        panelPosition.value = {
          top: adjustedTop,
          right: 0
        }
      }
      
      showCurrentPanel.value = true
      expandedHistoryId.value = null
    }
  }
}

function hideCurrentPanel() {
  showCurrentPanel.value = false
  selectedText.value = ''
  streamingAnswer.value = ''
  window.getSelection()?.removeAllRanges()
}

function showCardAnnotationInput() {
  showCardInput.value = true
  cardAnnotation.value = ''
  cardSuccess.value = false
}

function cancelCardCreation() {
  showCardInput.value = false
  cardAnnotation.value = ''
}

async function createCardWithAnnotation() {
  if (!selectedText.value || !sessionId.value) return
  
  cardCreating.value = true
  try {
    await api.createCard(sessionId.value, selectedText.value, cardAnnotation.value)
    cardSuccess.value = true
    await loadCards()
    
    setTimeout(() => {
      showCardInput.value = false
      cardSuccess.value = false
      cardAnnotation.value = ''
    }, 1500)
  } catch (error: any) {
    ElMessage.error(error.message || '创建卡片失败')
  }
  cardCreating.value = false
}

async function createCardFromSelection() {
  if (!selectedText.value || !sessionId.value) return
  
  try {
    const card = await api.createCard(sessionId.value, selectedText.value)
    ElMessage.success('已摘录为知识卡片')
    await loadCards()
    hideCurrentPanel()
  } catch (error: any) {
    ElMessage.error(error.message || '创建卡片失败')
  }
}

async function askQuestion(qType?: string) {
  if (!selectedText.value) {
    ElMessage.warning('请先选中文字')
    return
  }
  
  const actualQuestion = qType 
    ? quickQuestions.find(q => q.type === qType)?.template || '请解释这段内容'
    : question.value || '请解释这段内容'
  
  answering.value = true
  streamingAnswer.value = ''
  showCurrentPanel.value = true
  expandedHistoryId.value = null
  
  try {
    await sessionStore.askQuestionStream(actualQuestion, selectedText.value, (chunk: any) => {
      if (chunk.type === 'text') {
        streamingAnswer.value += chunk.content || ''
      }
    })
    question.value = ''
  } catch (error: any) {
    ElMessage.error(error.message || '提问失败')
  }
  
  answering.value = false
}

function toggleHistoryItem(id: string) {
  expandedHistoryId.value = expandedHistoryId.value === id ? null : id
}

async function deleteCard(cardId: string) {
  try {
    await api.deleteCard(cardId)
    ElMessage.success('卡片已删除')
    await loadCards()
  } catch (error: any) {
    ElMessage.error(error.message || '删除失败')
  }
}

function goBack() {
  router.push('/history')
}
</script>

<template>
  <div class="maphiver-app" :class="{ 'is-focus-mode': isFocusMode }" v-loading="loading">
    <nav class="top-nav">
      <div class="nav-left">
        <el-button :icon="ArrowLeft" @click="goBack" text size="small" class="nav-btn" v-if="!isFocusMode"></el-button>
        <span class="app-title" v-if="!isFocusMode">流式知识河</span>
      </div>
      <div class="nav-right">
        <el-button :icon="isDarkMode ? Sunny : Moon" @click="toggleTheme" text size="small" class="nav-btn" :title="isDarkMode ? '浅色模式' : '深色模式'"></el-button>
        <el-button :icon="isFocusMode ? Reading : FullScreen" @click="toggleFocusMode" text size="small" class="nav-btn" :title="isFocusMode ? '退出专注模式' : '专注模式'"></el-button>
      </div>
    </nav>

    <div class="sidebar-trigger" v-if="!isFocusMode" @mouseenter="sidebarHovered = true" @mouseleave="sidebarHovered = false">
      <div class="trigger-bar"></div>
    </div>
    
    <aside class="sidebar-hover" v-if="!isFocusMode" :class="{ 'is-visible': sidebarHovered }" @mouseenter="sidebarHovered = true" @mouseleave="sidebarHovered = false">
      <div class="sidebar-content">
        <div class="cards-section">
          <div class="section-header">
            <el-icon><Notebook /></el-icon>
            <span>知识卡片</span>
            <span class="section-count">{{ cards.length }}</span>
          </div>
          
          <el-scrollbar height="180px">
            <div v-if="cards.length > 0" class="cards-list">
              <div v-for="card in cards" :key="card.id" class="card-item">
                <div class="card-source">{{ card.source_text.slice(0, 60) }}{{ card.source_text.length > 60 ? '...' : '' }}</div>
                <div v-if="card.annotation" class="card-annotation">{{ card.annotation }}</div>
                <div class="card-actions">
                  <el-button size="small" text :icon="EditPen">编辑</el-button>
                  <el-button size="small" text :icon="Close" @click="deleteCard(card.id)">删除</el-button>
                </div>
              </div>
            </div>
          </el-scrollbar>
        </div>
        
        <div class="footprints-section" v-if="sessionId">
          <FootprintPanel :session-id="sessionId" />
        </div>
      </div>
    </aside>

    <div class="page-shell">

      <div class="scroll-container" ref="scrollContainerRef">
        <div v-if="parsing" class="parsing-view">
          <div class="parse-hero">
            <div class="parse-progress-panel">
              <div class="progress-bar">
                <el-progress :percentage="parseProgress" :stroke-width="6" :show-text="false" />
                <span class="progress-text">{{ parseProgress }}%</span>
              </div>
              <div class="parse-stage">{{ parseStage }}</div>
            </div>
          </div>
          
          <div class="parsing-layout">
            <div class="parsing-main">
              <div class="parsing-content">
                <div class="stream-output">
                  <div v-if="displayContent" class="stream-text" v-html="renderMarkdownWithLatex(displayContent)"></div>
                  <span v-if="parseStage.includes('格式化') && streamBuffer.length > 0" class="cursor-blink">█</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else-if="!hasDocument" class="upload-area">
          <div class="upload-content">
            <el-upload
              drag
              accept=".pdf,.doc,.docx"
              :auto-upload="false"
              :on-change="handleFileChange"
              :file-list="fileList"
              :limit="1"
              :disabled="uploading || parsing"
            >
              <el-icon class="upload-icon"><upload-filled /></el-icon>
              <div class="upload-text">拖拽文档文件到此处，或<em>点击上传</em></div>
              <template #tip>
                <div class="upload-tip">支持 PDF、DOC、DOCX 格式</div>
              </template>
            </el-upload>
            
            <el-button
              type="primary"
              :loading="uploading || parsing"
              :disabled="fileList.length === 0"
              @click="handleUpload"
              class="upload-btn"
            >
              {{ parsing ? parseStage : uploading ? '上传中...' : '开始解析' }}
            </el-button>
            
            <div v-if="parsing" class="parse-progress">
              <el-progress :percentage="parseProgress" :status="parseProgress === 100 ? 'success' : ''" />
            </div>
          </div>
        </div>
        
        <div v-else class="content-wrapper">
          <main class="main-column" ref="contentRef">
            <div class="doc-header">
              <span class="doc-title">{{ documentTitle }}</span>
            </div>
            
            <div class="breadcrumb-bar" :class="{ 'is-visible': showBreadcrumb && currentChapter }">
              <span class="breadcrumb-text">{{ currentChapter }}</span>
            </div>
            
            <div class="markdown-content" @mouseup="handleTextSelection">
              <div v-html="renderedMarkdown"></div>
              <div v-if="!documentStore.rawMarkdown && !loading" class="empty-content">
                文档内容为空
              </div>
            </div>
          </main>
          
          <aside class="qa-column">
            <div class="qa-panel">
              <div v-if="showCurrentPanel" class="current-panel" :style="{ top: panelPosition.top + 'px' }">
                <div class="current-header">
                  <span class="current-label">已选中 {{ selectedText.length }} 字</span>
                  <el-button size="small" text :icon="Close" @click="hideCurrentPanel" />
                </div>
                
                <div class="current-context">
                  <span class="context-quote">{{ selectedText.slice(0, 100) }}{{ selectedText.length > 100 ? '...' : '' }}</span>
                </div>
                
                <div class="quick-actions">
                  <el-button 
                    v-for="q in quickQuestions" 
                    :key="q.type"
                    size="small"
                    round
                    @click="askQuestion(q.type)"
                    :disabled="answering"
                  >
                    {{ q.label }}
                  </el-button>
                </div>

                <div class="question-composer">
                  <input
                    v-model="question"
                    type="text"
                    placeholder="补一句深挖..."
                    class="question-input"
                    @keyup.enter="askQuestion()"
                  />
                  <el-button size="small" type="primary" plain :disabled="answering || !selectedText" @click="askQuestion()">提问</el-button>
                </div>
                
                <div v-if="showCardInput" class="card-input-area">
                  <div class="card-input-field">
                    <input 
                      v-model="cardAnnotation"
                      type="text"
                      placeholder="添加批注..."
                      class="annotation-input"
                      @keyup.enter="createCardWithAnnotation"
                      @keyup.escape="cancelCardCreation"
                      :disabled="cardCreating"
                    />
                  </div>
                  <div v-if="cardSuccess" class="card-success">
                    <span class="success-icon">✓</span>
                    <span class="success-text">已汇入知识河</span>
                  </div>
                  <div v-else class="card-input-actions">
                    <el-button size="small" text @click="cancelCardCreation">取消</el-button>
                    <el-button size="small" type="primary" :loading="cardCreating" @click="createCardWithAnnotation">保存</el-button>
                  </div>
                </div>
                
                <div v-if="streamingAnswer" class="stream-area">
                  <div class="stream-label">AI 回复</div>
                  <div class="stream-content" v-html="renderMarkdownWithLatex(streamingAnswer)"></div>
                  <div v-if="answering" class="stream-loading">
                    <el-icon class="is-loading"><ChatDotRound /></el-icon>
                    <span>正在展开解释...</span>
                  </div>
                  <div v-if="!answering && streamingAnswer" class="stream-actions">
                    <el-button size="small" text :icon="EditPen" @click="createCardFromSelection">
                      摘录为卡片
                    </el-button>
                  </div>
                </div>
                
                <div v-else class="panel-actions">
                  <el-button size="small" :icon="EditPen" @click="showCardAnnotationInput">摘录卡片</el-button>
                </div>
              </div>
              
              <div class="history-section">
                <div class="history-header">
                  <div>
                    <div class="history-overline">Conversation Archive</div>
                    <span>历史问答</span>
                  </div>
                  <span class="history-count">{{ qaMessages.length }}</span>
                </div>
                
                <div v-if="qaMessages.length === 0" class="history-empty"></div>
                
                <div v-else class="history-list">
                  <div 
                    v-for="msg in qaMessages" 
                    :key="msg.id" 
                    class="history-item"
                    :class="{ 'is-expanded': expandedHistoryId === msg.id }"
                  >
                    <div class="history-question" @click="toggleHistoryItem(msg.id)">
                      <el-icon><QuestionFilled /></el-icon>
                      <span class="question-text">{{ msg.question }}</span>
                      <span class="expand-icon">{{ expandedHistoryId === msg.id ? '▼' : '▶' }}</span>
                    </div>
                    <div v-if="expandedHistoryId === msg.id" class="history-answer">
                      <div class="history-context">“{{ msg.selected_text.slice(0, 90) }}{{ msg.selected_text.length > 90 ? '...' : '' }}”</div>
                      <div v-html="renderMarkdownWithLatex(msg.answer)"></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.maphiver-app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: var(--bg-main);
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: var(--bg-main);
  border-bottom: 1px solid var(--border-color);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.nav-left,
.nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-primary);
  font-family: var(--font-serif);
  letter-spacing: 0.5px;
}

.nav-btn {
  color: var(--text-secondary);
}

.nav-btn:hover {
  color: var(--text-primary);
  background: var(--bg-hover);
}

.sidebar-trigger {
  position: fixed;
  left: 0;
  top: 0;
  width: 8px;
  height: 100vh;
  z-index: 100;
  cursor: pointer;
}

.trigger-bar {
  width: 4px;
  height: 100%;
  background: var(--border-color);
  transition: background var(--transition-fast);
}

.sidebar-trigger:hover .trigger-bar {
  background: var(--text-accent);
}

.sidebar-hover {
  position: fixed;
  left: 0;
  top: 0;
  width: 260px;
  height: 100vh;
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  z-index: 99;
  transform: translateX(-260px);
  transition: transform var(--transition-normal);
  display: flex;
  flex-direction: column;
  padding-top: 48px;
}

.sidebar-hover.is-visible {
  transform: translateX(0);
}

.sidebar-content {
  flex: 1;
  padding: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.cards-section {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.section-count {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  background: var(--bg-hover);
  padding: 2px 8px;
  border-radius: 10px;
}

.cards-loading, .cards-empty {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
  font-size: var(--font-size-xs);
}

.cards-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-item {
  padding: 10px;
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.card-source {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  line-height: 1.5;
}

.card-annotation {
  font-size: var(--font-size-xs);
  color: var(--text-accent);
  margin-top: 6px;
  padding: 4px 8px;
  background: color-mix(in srgb, var(--text-accent) 15%, transparent);
  border-radius: var(--radius-sm);
}

.card-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
}

.footprints-section {
  flex: 1;
  min-height: 180px;
}

.page-shell {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.upload-area {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 40px;
}

.upload-content {
  max-width: 480px;
  width: 100%;
  padding: 40px;
}

.upload-icon {
  font-size: 48px;
  color: var(--text-accent);
}

.upload-text {
  margin-top: 12px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.upload-text em {
  color: var(--text-accent);
}

.upload-tip {
  margin-top: 8px;
  color: var(--text-muted);
  font-size: var(--font-size-xs);
}

.upload-btn {
  width: 100%;
  margin-top: 20px;
}

.parse-progress {
  margin-top: 16px;
}

.content-wrapper {
  display: flex;
  min-height: calc(100vh - 48px);
}

.main-column {
  flex: 1;
  min-width: 600px;
  padding: 0 10vw;
  transition: padding var(--transition-normal);
}

.maphiver-app.is-focus-mode .main-column {
  padding: 0 20vw;
}

.maphiver-app.is-focus-mode .qa-column {
  display: none;
}

.doc-header {
  padding: 16px 0;
  border-bottom: 1px solid var(--border-light);
  margin-bottom: 24px;
}

.doc-title {
  font-size: var(--font-size-lg);
  color: var(--text-primary);
  font-weight: 500;
}

.breadcrumb-bar {
  position: sticky;
  top: 0;
  background: var(--bg-main);
  padding: 8px 0;
  margin-bottom: 16px;
  opacity: 0;
  transition: opacity var(--transition-fast);
  z-index: 10;
}

.breadcrumb-bar.is-visible {
  opacity: 1;
}

.breadcrumb-text {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.markdown-content {
  padding-bottom: 100px;
}

.markdown-content :deep(h1) {
  font-size: 2em;
  margin: 1.4em 0 0.7em;
  color: var(--text-primary);
  font-weight: 700;
  border-bottom: 2px solid var(--text-accent);
  padding-bottom: 0.4em;
  letter-spacing: -0.02em;
}

.markdown-content :deep(h2) {
  font-size: 1.6em;
  margin: 1.2em 0 0.6em;
  color: var(--text-primary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.3em;
  letter-spacing: -0.01em;
}

.markdown-content :deep(h3) {
  font-size: 1.3em;
  margin: 1em 0 0.5em;
  color: var(--text-primary);
  font-weight: 600;
}

.markdown-content :deep(h4) {
  font-size: 1.15em;
  margin: 0.8em 0 0.4em;
  color: var(--text-primary);
  font-weight: 600;
}

.markdown-content :deep(p) {
  margin: 0.9em 0;
  line-height: 1.9;
  color: var(--text-primary);
  font-family: var(--font-serif);
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 0.8em 0;
  padding-left: 1.8em;
  line-height: 1.8;
}

.markdown-content :deep(li) {
  margin: 0.3em 0;
}

.markdown-content :deep(li)::marker {
  color: var(--text-accent);
}

.markdown-content :deep(blockquote) {
  margin: 1em 0;
  padding: 0.8em 1.2em;
  border-left: 4px solid var(--text-accent);
  background: var(--bg-hover);
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
}

.markdown-content :deep(blockquote p) {
  margin: 0.3em 0;
}

.markdown-content :deep(strong) {
  color: var(--text-accent);
  font-weight: 600;
}

.markdown-content :deep(em) {
  color: var(--text-secondary);
  font-style: italic;
}

.markdown-content :deep(code) {
  background: var(--bg-hover);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'Consolas', 'Monaco', monospace;
}

.markdown-content :deep(pre) {
  background: var(--bg-sidebar);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1em 0;
  border: 1px solid var(--border-color);
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.85em;
  line-height: 1.6;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid var(--border-color);
  padding: 10px 14px;
  text-align: left;
}

.markdown-content :deep(th) {
  background: var(--bg-sidebar);
  font-weight: 600;
  color: var(--text-primary);
}

.markdown-content :deep(tr:nth-child(even)) {
  background: var(--bg-hover);
}

.markdown-content :deep(hr) {
  border: none;
  height: 1px;
  background: var(--border-color);
  margin: 1.5em 0;
}

.markdown-content :deep(a) {
  color: var(--text-accent);
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(.katex) {
  font-size: 1.1em;
}

.markdown-content :deep(.katex-display) {
  margin: 1.2em 0;
  overflow-x: auto;
  padding: 0.5em 0;
}

.markdown-content :deep(.katex-display > .katex) {
  text-align: center;
}

.markdown-content :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 1em 0;
}

.empty-content {
  text-align: center;
  color: var(--text-secondary);
  padding: 100px 0;
}

.qa-column {
  width: 360px;
  padding: 16px;
  padding-left: 0;
}

.qa-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.current-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 16px;
  position: fixed;
  right: 20px;
  width: 420px;
  z-index: 100;
  box-shadow: var(--shadow-md);
  max-height: 75vh;
  overflow-y: auto;
  transition: all var(--transition-fast);
}

.current-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.current-label {
  font-size: var(--font-size-sm);
  color: var(--text-accent);
  font-weight: 500;
}

.current-context {
  margin-bottom: 12px;
}

.context-quote {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  background: var(--bg-hover);
  padding: 8px 12px;
  border-radius: 6px;
  display: block;
  line-height: 1.5;
}

.quick-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.card-input-area {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
}

.card-input-field {
  margin-bottom: 8px;
}

.annotation-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: var(--font-size-sm);
  background: var(--bg-main);
  color: var(--text-primary);
}

.annotation-input:focus {
  outline: none;
  border-color: var(--text-accent);
}

.card-success {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--success-color);
}

.card-input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.stream-area {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
}

.stream-label {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  margin-bottom: 8px;
}

.stream-content {
  font-size: var(--font-size-sm);
  line-height: 1.6;
  color: var(--text-primary);
}

.stream-content :deep(p) {
  margin: 0.5em 0;
}

.stream-content :deep(h1) {
  font-size: 1.4em;
  margin: 0.8em 0 0.4em;
  color: var(--text-primary);
  font-weight: 600;
}

.stream-content :deep(h2) {
  font-size: 1.2em;
  margin: 0.6em 0 0.3em;
  color: var(--text-primary);
  font-weight: 600;
}

.stream-content :deep(h3) {
  font-size: 1.1em;
  margin: 0.5em 0 0.2em;
  color: var(--text-primary);
  font-weight: 600;
}

.stream-content :deep(ul),
.stream-content :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.5em;
}

.stream-content :deep(li) {
  margin: 0.2em 0;
}

.stream-content :deep(code) {
  background: var(--bg-hover);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}

.stream-content :deep(pre) {
  background: var(--bg-sidebar);
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.8em 0;
}

.stream-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.stream-content :deep(blockquote) {
  border-left: 3px solid var(--text-accent);
  padding-left: 12px;
  margin: 0.8em 0;
  color: var(--text-secondary);
  background: var(--bg-hover);
  border-radius: 0 8px 8px 0;
}

.stream-content :deep(strong) {
  color: var(--text-accent);
  font-weight: 600;
}

.stream-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.8em 0;
}

.stream-content :deep(th),
.stream-content :deep(td) {
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  text-align: left;
}

.stream-content :deep(th) {
  background: var(--bg-sidebar);
  font-weight: 600;
}

.stream-content :deep(.katex) {
  font-size: 1.1em;
}

.stream-content :deep(.katex-display) {
  margin: 1em 0;
  overflow-x: auto;
  padding: 0.5em 0;
}

.stream-content :deep(.katex-display > .katex) {
  text-align: center;
}

.stream-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-accent);
  margin-top: 8px;
}

.stream-actions {
  margin-top: 12px;
}

.panel-actions {
  display: flex;
  justify-content: flex-end;
}

.history-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 12px;
  box-shadow: var(--shadow-sm);
}

.history-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.history-count {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  background: var(--bg-hover);
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.history-empty {
  text-align: center;
  color: var(--text-secondary);
  padding: 20px;
  font-size: var(--font-size-xs);
}

.history-empty .hint {
  margin-top: 8px;
  color: var(--text-muted);
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  border-radius: var(--radius-sm);
  background: var(--bg-card);
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.history-question {
  padding: 10px 12px;
  background: var(--bg-hover);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.history-question:hover {
  background: var(--bg-active);
}

.history-answer {
  padding: 10px 12px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-light);
}

.history-question {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  cursor: pointer;
  font-size: var(--font-size-xs);
}

.question-text {
  flex: 1;
  color: var(--text-secondary);
}

.expand-icon {
  color: var(--text-muted);
  font-size: 10px;
}

.history-answer {
  padding: 10px;
  padding-top: 0;
  font-size: var(--font-size-xs);
  color: var(--text-primary);
  line-height: 1.6;
}

.history-answer :deep(p) {
  margin: 0.3em 0;
}

.history-answer :deep(h1) {
  font-size: 1.3em;
  margin: 0.6em 0 0.3em;
  font-weight: 600;
}

.history-answer :deep(h2) {
  font-size: 1.1em;
  margin: 0.5em 0 0.2em;
  font-weight: 600;
}

.history-answer :deep(h3) {
  font-size: 1em;
  margin: 0.4em 0 0.2em;
  font-weight: 600;
}

.history-answer :deep(ul),
.history-answer :deep(ol) {
  margin: 0.4em 0;
  padding-left: 1.2em;
}

.history-answer :deep(li) {
  margin: 0.15em 0;
}

.history-answer :deep(code) {
  background: var(--bg-hover);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 0.9em;
}

.history-answer :deep(pre) {
  background: var(--bg-sidebar);
  padding: 8px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 0.5em 0;
}

.history-answer :deep(pre code) {
  background: transparent;
  padding: 0;
}

.history-answer :deep(blockquote) {
  border-left: 2px solid var(--text-accent);
  padding-left: 8px;
  margin: 0.5em 0;
  color: var(--text-secondary);
  background: var(--bg-hover);
  border-radius: 0 6px 6px 0;
}

.history-answer :deep(strong) {
  color: var(--text-accent);
  font-weight: 600;
}

.history-answer :deep(.katex) {
  font-size: 1.05em;
}

.history-answer :deep(.katex-display) {
  margin: 0.5em 0;
  overflow-x: auto;
}

.history-answer :deep(.katex-display > .katex) {
  text-align: center;
}

.parsing-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.parse-header {
  position: sticky;
  top: 0;
  background: var(--bg-main);
  padding: 12px 24px;
  border-bottom: 1px solid var(--border-color);
  z-index: 20;
}

.progress-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar .el-progress {
  flex: 1;
}

.progress-text {
  font-size: var(--font-size-sm);
  color: var(--text-accent);
  font-weight: 500;
  min-width: 40px;
}

.parse-stage {
  margin-top: 8px;
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.parsing-layout {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px;
}

.parsing-main {
  flex: 1;
  min-width: 0;
}

.parsing-content {
  flex: 1;
  padding: 24px 10vw;
  overflow-y: auto;
}

.stream-output {
  font-size: var(--font-size-base);
  line-height: 1.8;
  color: var(--text-primary);
}

.stream-text {
  white-space: pre-wrap;
}

.stream-text :deep(h1) {
  font-size: 1.8em;
  margin: 1.2em 0 0.6em;
  color: var(--text-primary);
  font-weight: 700;
  border-bottom: 2px solid var(--text-accent);
  padding-bottom: 0.3em;
}

.stream-text :deep(h2) {
  font-size: 1.4em;
  margin: 1em 0 0.5em;
  color: var(--text-primary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.2em;
}

.stream-text :deep(h3) {
  font-size: 1.2em;
  margin: 0.8em 0 0.4em;
  color: var(--text-primary);
  font-weight: 600;
}

.stream-text :deep(h4) {
  font-size: 1.1em;
  margin: 0.6em 0 0.3em;
  color: var(--text-primary);
  font-weight: 600;
}

.stream-text :deep(p) {
  margin: 0.8em 0;
  line-height: 1.8;
  color: var(--text-primary);
}

.stream-text :deep(ul),
.stream-text :deep(ol) {
  margin: 0.8em 0;
  padding-left: 1.8em;
  line-height: 1.8;
}

.stream-text :deep(li) {
  margin: 0.3em 0;
}

.stream-text :deep(li)::marker {
  color: var(--text-accent);
}

.stream-text :deep(blockquote) {
  margin: 1em 0;
  padding: 0.8em 1.2em;
  border-left: 4px solid var(--text-accent);
  background: var(--bg-hover);
  border-radius: 0 8px 8px 0;
  color: var(--text-secondary);
}

.stream-text :deep(blockquote p) {
  margin: 0.3em 0;
}

.stream-text :deep(strong) {
  color: var(--text-accent);
  font-weight: 600;
}

.stream-text :deep(em) {
  color: var(--text-secondary);
  font-style: italic;
}

.stream-text :deep(code) {
  background: var(--bg-hover);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: 'Consolas', 'Monaco', monospace;
}

.stream-text :deep(pre) {
  background: var(--bg-sidebar);
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1em 0;
  border: 1px solid var(--border-color);
}

.stream-text :deep(pre code) {
  background: none;
  padding: 0;
  font-size: 0.85em;
  line-height: 1.6;
}

.stream-text :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}

.stream-text :deep(th),
.stream-text :deep(td) {
  border: 1px solid var(--border-color);
  padding: 10px 14px;
  text-align: left;
}

.stream-text :deep(th) {
  background: var(--bg-sidebar);
  font-weight: 600;
  color: var(--text-primary);
}

.stream-text :deep(tr:nth-child(even)) {
  background: var(--bg-hover);
}

.stream-text :deep(hr) {
  border: none;
  height: 1px;
  background: var(--border-color);
  margin: 1.5em 0;
}

.stream-text :deep(a) {
  color: var(--text-accent);
  text-decoration: none;
}

.stream-text :deep(a:hover) {
  text-decoration: underline;
}

.stream-text :deep(.katex) {
  font-size: 1.1em;
}

.stream-text :deep(.katex-display) {
  margin: 1.2em 0;
  overflow-x: auto;
  padding: 0.5em 0;
}

.stream-text :deep(.katex-display > .katex) {
  text-align: center;
}

.stream-text :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  margin: 1em 0;
  display: block;
}

.stream-waiting {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.waiting-text {
  color: var(--text-muted);
  font-size: var(--font-size-sm);
}

.cursor-blink {
  color: var(--text-accent);
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
