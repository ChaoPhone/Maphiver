<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore, useDocumentStore } from '@/stores'
import { marked } from 'marked'
import katex from 'katex'
import { ElMessage, ElScrollbar, ElUpload, ElProgress, ElIcon } from 'element-plus'
import { ChatDotRound, Document, UploadFilled, Notebook, EditPen, QuestionFilled, Close } from '@element-plus/icons-vue'
import type { KnowledgeCard } from '@/types'
import * as api from '@/api'
import FootprintPanel from '@/components/FootprintPanel.vue'
import { extractLatexBlocks, preprocessLatexFormula } from '@/utils/latex'

marked.setOptions({ breaks: true, gfm: true })

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
const fileList = ref<any[]>([])

const selectedText = ref('')
const selectedRange = ref<{ start: number; end: number; rect: DOMRect | null }>({ start: 0, end: 0, rect: null })
const question = ref('')
const answering = ref(false)
const streamingAnswer = ref('')
const showSelectionPopup = ref(false)
const showQAPanel = ref(false)
const contentRef = ref<HTMLElement | null>(null)
const cards = ref<KnowledgeCard[]>([])
const cardsLoading = ref(false)
const sidebarCollapsed = ref(false)
const showCardInput = ref(false)
const cardAnnotation = ref('')
const cardCreating = ref(false)
const cardSuccess = ref(false)
const currentChapter = ref('')
const showBreadcrumb = ref(false)

const sessionId = computed(() => route.params.sessionId as string)
const hasDocument = computed(() => !!sessionStore.currentSession?.document_id)
const qaMessages = computed(() => sessionStore.qaMessages)

const renderedMarkdown = computed(() => {
  return renderMarkdownWithLatex(documentStore.rawMarkdown)
})

const quickQuestions = [
  { type: 'explain', label: '解释', template: '请解释这段内容' },
  { type: 'summary', label: '总结', template: '请总结这段内容的核心要点' },
  { type: 'example', label: '举例', template: '请举例说明这个概念' },
  { type: 'compare', label: '对比', template: '请对比分析这两个概念' },
]

onMounted(async () => {
  if (sessionId.value) {
    await loadSessionData()
  }
  setupScrollObserver()
})

onUnmounted(() => {
  removeScrollObserver()
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

async function handleUpload() {
  if (fileList.value.length === 0 || !fileList.value[0].raw) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  parseProgress.value = 0
  parseStage.value = ''
  
  try {
    const result = await documentStore.uploadFile(fileList.value[0].raw)
    ElMessage.success('上传成功')
    
    uploading.value = false
    parsing.value = true
    parseStage.value = '提取文本...'
    parseProgress.value = 10
    
    await documentStore.parseDocument(result.id, (data: any) => {
      if (data.type === 'progress') {
        parseStage.value = getStageLabel(data.stage)
        parseProgress.value = data.progress || parseProgress.value
      }
    })
    
    parseProgress.value = 100
    parseStage.value = '解析完成'
    ElMessage.success('解析完成')
    
    const session = await sessionStore.createSession(result.id)
    router.push(`/read/${session.id}`)
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
    if (text.length > 10) {
      selectedText.value = text
      
      const range = selection.getRangeAt(0)
      const rect = range.getBoundingClientRect()
      selectedRange.value = {
        start: range.startOffset,
        end: range.endOffset,
        rect: rect
      }
      
      showSelectionPopup.value = true
      showQAPanel.value = true
      
      nextTick(() => {
        positionSelectionPopup(rect)
      })
    }
  }
}

function positionSelectionPopup(rect: DOMRect) {
  const popup = document.querySelector('.selection-popup') as HTMLElement
  if (popup && rect) {
    const containerRect = contentRef.value?.getBoundingClientRect()
    if (containerRect) {
      popup.style.top = `${rect.top - containerRect.top - 50}px`
      popup.style.left = `${rect.right - containerRect.left + 10}px`
    }
  }
}

function hideSelectionPopup() {
  showSelectionPopup.value = false
  selectedText.value = ''
  window.getSelection()?.removeAllRanges()
}

function showCardAnnotationInput() {
  showCardInput.value = true
  cardAnnotation.value = ''
  cardSuccess.value = false
  showSelectionPopup.value = false
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
      selectedText.value = ''
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
    hideSelectionPopup()
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
  showQAPanel.value = true
  showSelectionPopup.value = false
  
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

function closeAIReply() {
  showQAPanel.value = false
  streamingAnswer.value = ''
  selectedText.value = ''
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

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="maphiver-app" v-loading="loading" element-loading-text="正在加载...">
    <aside class="sidebar" :class="{ 'is-collapsed': sidebarCollapsed }">
      <div class="sidebar-header">
        <el-button :icon="Document" @click="goBack" text size="small">返回</el-button>
        <el-button 
          :icon="sidebarCollapsed ? 'Expand' : 'Fold'" 
          @click="toggleSidebar" 
          text 
          size="small"
        />
      </div>
      
      <div class="sidebar-content">
        <div class="cards-section">
          <div class="section-header">
            <el-icon><Notebook /></el-icon>
            <span>知识卡片</span>
            <span class="section-count">{{ cards.length }}</span>
          </div>
          
          <el-scrollbar height="180px">
            <div v-if="cardsLoading" class="cards-loading">加载中...</div>
            <div v-else-if="cards.length === 0" class="cards-empty">选中文字后点击"摘录"</div>
            <div v-else class="cards-list">
              <div v-for="card in cards" :key="card.id" class="card-item">
                <div class="card-source">{{ card.source_text.slice(0, 60) }}...</div>
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

    <main class="reading-zone">
      <div v-if="!hasDocument" class="upload-area">
        <div class="upload-content">
          <el-upload
            drag
            accept=".pdf"
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :limit="1"
            :disabled="uploading || parsing"
          >
            <el-icon class="upload-icon"><upload-filled /></el-icon>
            <div class="upload-text">拖拽PDF文件到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="upload-tip">仅支持PDF格式</div>
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
      
      <div v-else class="reading-area" ref="contentRef">
        <div class="doc-header">
          <span class="doc-title">{{ sessionStore.currentSession?.document?.filename || '流式知识河' }}</span>
        </div>
        
        <div class="breadcrumb-bar" :class="{ 'is-visible': showBreadcrumb && currentChapter }">
          <span class="breadcrumb-text">{{ currentChapter }}</span>
        </div>
        
        <el-scrollbar>
          <div class="markdown-content" @mouseup="handleTextSelection">
            <div v-html="renderedMarkdown"></div>
            <div v-if="!documentStore.rawMarkdown && !loading" class="empty-content">
              文档内容为空
            </div>
          </div>
        </el-scrollbar>
        
        <div v-if="showSelectionPopup" class="selection-popup">
          <div class="popup-context">
            <span class="context-label">已选中 {{ selectedText.length }} 字</span>
          </div>
          <div class="popup-actions">
            <el-button size="small" :icon="EditPen" @click="showCardAnnotationInput">摘录卡片</el-button>
            <el-button size="small" type="primary" :icon="QuestionFilled" @click="askQuestion()">向AI提问</el-button>
          </div>
          <div class="quick-questions">
            <el-button 
              v-for="q in quickQuestions" 
              :key="q.type"
              size="small"
              round
              @click="askQuestion(q.type)"
            >
              {{ q.label }}
            </el-button>
          </div>
        </div>
        
        <div v-if="showCardInput" class="card-input-inline">
          <div class="card-input-context">
            <span class="context-label">摘录内容：</span>
            <span class="context-preview">{{ selectedText.slice(0, 50) }}{{ selectedText.length > 50 ? '...' : '' }}</span>
          </div>
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
            <span class="success-icon">✅</span>
            <span class="success-text">已汇入知识河</span>
          </div>
          <div v-else class="card-input-actions">
            <el-button size="small" text @click="cancelCardCreation">取消</el-button>
            <el-button size="small" type="primary" :loading="cardCreating" @click="createCardWithAnnotation">保存</el-button>
          </div>
        </div>
      </div>
    </main>

    <aside v-show="showQAPanel" class="qa-panel">
      <div class="qa-header">
        <span class="qa-title">AI交互</span>
        <el-button size="small" text :icon="Close" @click="closeAIReply" />
      </div>
      
      <div v-if="selectedText && !streamingAnswer" class="qa-context">
        <div class="context-quote">{{ selectedText.slice(0, 100) }}{{ selectedText.length > 100 ? '...' : '' }}</div>
      </div>
      
      <div class="qa-stream" v-if="streamingAnswer">
        <div class="stream-content" v-html="renderMarkdownWithLatex(streamingAnswer)"></div>
        <div v-if="answering" class="stream-loading">
          <el-icon class="is-loading"><ChatDotRound /></el-icon>
          <span>回复中...</span>
        </div>
        <div v-if="!answering && streamingAnswer" class="stream-actions">
          <el-button size="small" text :icon="EditPen" @click="createCardFromSelection">
            摘录为知识卡
          </el-button>
        </div>
      </div>
      
      <div class="qa-history" v-if="qaMessages.length > 0">
        <div class="history-header">
          <span>历史问答</span>
          <span class="history-count">{{ qaMessages.length }}</span>
        </div>
        <el-scrollbar height="calc(100vh - 280px)">
          <div v-for="msg in qaMessages" :key="msg.id" class="qa-item">
            <div class="qa-question">
              <el-icon><QuestionFilled /></el-icon>
              <span>{{ msg.question }}</span>
            </div>
            <div class="qa-answer" v-html="renderMarkdownWithLatex(msg.answer)"></div>
          </div>
        </el-scrollbar>
      </div>
      
      <div v-else-if="!streamingAnswer" class="qa-empty">
        <p>选中文字后点击"向AI提问"</p>
        <p class="hint">AI回复将在此处显示</p>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.maphiver-app {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: var(--bg-main);
}

.sidebar {
  width: var(--sidebar-width);
  background-color: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width var(--transition-normal);
}

.sidebar.is-collapsed {
  width: 0;
  border: none;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
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
  background: var(--bg-hover);
  border-radius: 6px;
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
  background: rgba(37, 99, 235, 0.1);
  border-radius: 4px;
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

.reading-zone {
  flex: 1;
  min-width: var(--reading-min-width);
  overflow-y: auto;
  padding: 0 var(--reading-padding);
  scroll-behavior: smooth;
  display: flex;
  flex-direction: column;
}

.upload-area {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  flex: 1;
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

.reading-area {
  height: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
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
  position: fixed;
  top: 0;
  left: var(--sidebar-width);
  right: 0;
  padding: 8px 20px;
  background: linear-gradient(to bottom, var(--bg-main), transparent);
  opacity: 0;
  transition: opacity var(--transition-normal);
  z-index: 50;
  pointer-events: none;
}

.breadcrumb-bar.is-visible {
  opacity: 1;
}

.breadcrumb-text {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.markdown-content {
  padding-bottom: 60px;
  line-height: var(--line-height);
  min-height: 100%;
}

.markdown-content :deep(h1) {
  font-size: 1.75em;
  margin-bottom: 1em;
  color: var(--text-primary);
}

.markdown-content :deep(h2) {
  font-size: 1.5em;
  margin-bottom: 0.75em;
  color: var(--text-primary);
}

.markdown-content :deep(h3) {
  font-size: 1.25em;
  margin-bottom: 0.5em;
  color: var(--text-primary);
}

.markdown-content :deep(p) {
  margin-bottom: var(--paragraph-spacing);
  color: var(--text-primary);
}

.markdown-content :deep(.katex-display) {
  max-width: 100%;
  overflow-x: auto;
  padding: 12px 0;
  margin: 1em 0;
}

.empty-content {
  text-align: center;
  padding: 60px;
  color: var(--text-secondary);
}

.selection-popup {
  position: absolute;
  background: var(--bg-main);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  box-shadow: var(--shadow-md);
  z-index: 100;
  min-width: 200px;
}

.popup-context {
  margin-bottom: 10px;
}

.context-label {
  font-size: var(--font-size-xs);
  color: var(--text-accent);
}

.popup-actions {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.quick-questions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.qa-panel {
  width: var(--qa-panel-width);
  background-color: var(--bg-sidebar);
  border-left: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.qa-title {
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  font-weight: 500;
}

.qa-context {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
}

.context-quote {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  line-height: 1.5;
  padding-left: 12px;
  border-left: 2px solid var(--text-accent);
  background: rgba(37, 99, 235, 0.05);
  padding: 8px 12px;
  border-radius: 4px;
}

.qa-stream {
  padding: 16px;
  flex: 1;
  overflow-y: auto;
}

.stream-content {
  font-size: var(--font-size-sm);
  line-height: 1.6;
  color: var(--text-primary);
}

.stream-content :deep(.katex-display) {
  overflow-x: auto;
  margin: 0.5em 0;
}

.stream-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 0;
  color: var(--text-accent);
  font-size: var(--font-size-xs);
}

.stream-actions {
  padding-top: 12px;
  border-top: 1px solid var(--border-light);
  margin-top: 12px;
}

.qa-history {
  flex: 1;
  padding: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.history-count {
  color: var(--text-muted);
}

.qa-item {
  padding: 12px;
  margin-bottom: 12px;
  background: var(--bg-hover);
  border-radius: 6px;
}

.qa-question {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: var(--font-size-xs);
  color: var(--text-accent);
  margin-bottom: 8px;
}

.qa-answer {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  line-height: 1.5;
}

.qa-answer :deep(.katex-display) {
  overflow-x: auto;
}

.qa-empty {
  text-align: center;
  color: var(--text-secondary);
  padding: 40px 16px;
  font-size: var(--font-size-xs);
}

.qa-empty .hint {
  color: var(--text-muted);
  margin-top: 6px;
}

.card-input-inline {
  position: absolute;
  background: var(--bg-main);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 12px;
  box-shadow: var(--shadow-md);
  z-index: 100;
  min-width: 280px;
  max-width: 400px;
}

.card-input-context {
  margin-bottom: 10px;
}

.card-input-context .context-label {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.card-input-context .context-preview {
  font-size: var(--font-size-xs);
  color: var(--text-primary);
  display: block;
  margin-top: 4px;
  padding: 6px 10px;
  background: rgba(37, 99, 235, 0.05);
  border-radius: 4px;
  border-left: 2px solid var(--text-accent);
}

.card-input-field {
  margin-bottom: 10px;
}

.annotation-input {
  width: 100%;
  border: none;
  border-bottom: 1px solid var(--border-color);
  background: transparent;
  padding: 8px 0;
  font-size: var(--font-size-sm);
  color: var(--text-primary);
  outline: none;
  transition: border-color var(--transition-fast);
}

.annotation-input:focus {
  border-bottom-color: var(--text-accent);
}

.annotation-input::placeholder {
  color: var(--text-muted);
}

.card-success {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
}

.card-success .success-icon {
  font-size: 14px;
}

.card-success .success-text {
  font-size: var(--font-size-xs);
  color: #059669;
}

.card-input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>