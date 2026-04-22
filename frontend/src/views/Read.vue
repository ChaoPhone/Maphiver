<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore, useDocumentStore } from '@/stores'
import { ElMessage, ElButton } from 'element-plus'
import { ArrowLeft, Sunny, Moon, FullScreen, Reading } from '@element-plus/icons-vue'
import DocumentUploader from '@/components/DocumentUploader.vue'
import ParsingProgress from '@/components/ParsingProgress.vue'
import FormulaRenderer from '@/components/FormulaRenderer.vue'
import QAPanel from '@/components/QAPanel.vue'
import QAHistory from '@/components/QAHistory.vue'
import LeftSidebar from '@/components/LeftSidebar.vue'
import * as api from '@/api'

const route = useRoute()
const router = useRouter()
const sessionStore = useSessionStore()
const documentStore = useDocumentStore()

const loading = ref(false)
const parsing = ref(false)
const parseProgress = ref(0)
const parseStage = ref('')
const displayContent = ref('')
let streamBuffer = ''
let displayTimer: number | null = null

const isDarkMode = ref(false)
const isFocusMode = ref(false)
const sidebarHovered = ref(false)
const showQAPanel = ref(false)
const selectedText = ref('')
const panelPosition = ref({ top: 0, right: 0 })
const currentChapter = ref('')
const showBreadcrumb = ref(false)
const contentRef = ref<HTMLElement | null>(null)
const scrollContainerRef = ref<HTMLElement | null>(null)

const sessionId = computed(() => route.params.sessionId as string)
const hasDocument = computed(() => !!sessionStore.currentSession?.document_id)
const qaMessages = computed(() => sessionStore.qaMessages)
const documentTitle = computed(() => sessionStore.currentSession?.document?.filename || '流式知识河')

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

onMounted(async () => {
  const savedTheme = localStorage.getItem('maphiver-theme')
  if (savedTheme === 'dark') {
    isDarkMode.value = true
    document.documentElement.setAttribute('data-theme', 'dark')
  }
  
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
          currentChapter.value = heading.textContent || ''
          showBreadcrumb.value = true
        }
      })
    },
    { root: null, rootMargin: '-80px 0px -80% 0px', threshold: 0 }
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
  headings.forEach((heading) => scrollObserver!.observe(heading))
}

watch(() => documentStore.rawMarkdown, () => {
  nextTick(() => observeHeadings())
})

async function loadSessionData() {
  loading.value = true
  try {
    await sessionStore.loadSession(sessionId.value)
    if (sessionStore.currentSession?.document_id) {
      // 先尝试加载已解析的内容
      const parsedContent = await documentStore.loadParsedContent(sessionStore.currentSession.document_id)
      
      if (parsedContent && parsedContent.raw_markdown) {
        // 已有解析内容，直接显示
        parsing.value = false
      } else {
        // 没有解析内容，需要重新解析
        parsing.value = true
        parseProgress.value = 10
        parseStage.value = 'extracting'
        displayContent.value = ''
        streamBuffer = ''

        await documentStore.parseDocument(sessionStore.currentSession.document_id, (data: any) => {
          if (data.type === 'progress') {
            parseStage.value = data.stage || ''
            parseProgress.value = data.progress || parseProgress.value
          } else if (data.type === 'text' && data.content) {
            streamBuffer += data.content
            if (!displayTimer) startCharByCharDisplay()
            parseStage.value = 'formatting'
          }
        })

        parseProgress.value = 100
        parseStage.value = 'done'
        parsing.value = false
      }
    }
  } catch (error) {
    ElMessage.error('加载失败')
    parsing.value = false
  }
  loading.value = false
}

function startCharByCharDisplay() {
  if (displayTimer) clearInterval(displayTimer)
  displayTimer = window.setInterval(() => {
    if (streamBuffer.length > 0) {
      displayContent.value += streamBuffer.charAt(0)
      streamBuffer = streamBuffer.slice(1)
    } else if (!parsing.value) {
      if (displayTimer) {
        clearInterval(displayTimer)
        displayTimer = null
      }
    }
  }, 30)
}

async function handleUpload(documentId: string, newSessionId: string) {
  parsing.value = true
  parseProgress.value = 10
  parseStage.value = 'extracting'
  displayContent.value = ''
  streamBuffer = ''
  
  try {
    await documentStore.parseDocument(documentId, (data: any) => {
      if (data.type === 'progress') {
        parseStage.value = data.stage || ''
        parseProgress.value = data.progress || parseProgress.value
      } else if (data.type === 'text' && data.content) {
        streamBuffer += data.content
        if (!displayTimer) startCharByCharDisplay()
        parseStage.value = 'formatting'
      }
    })
    
    parseProgress.value = 100
    parseStage.value = 'done'
    ElMessage.success('解析完成')
    
    await sessionStore.loadSession(newSessionId)
    router.push(`/read/${newSessionId}`)
  } catch (error: any) {
    ElMessage.error(error.message || '解析失败')
  }
  parsing.value = false
}

function handleSelection(text: string, range: { start: number; end: number; rect: DOMRect | null; firstLineRect?: DOMRect | null }) {
  selectedText.value = text

  // 使用 firstLineRect（如果有的话）来定位到第一行右侧
  const targetRect = range.firstLineRect || range.rect
  const scrollRect = scrollContainerRef.value?.getBoundingClientRect()

  if (scrollRect && targetRect && targetRect.width > 0 && targetRect.height > 0) {
    const panelWidth = 400 // QA面板宽度
    const panelHeight = 500 // 预估面板高度
    const gap = 16 // 与文字的间距
    const viewportWidth = window.innerWidth
    const viewportHeight = window.innerHeight

    // 计算面板左侧位置：选区右侧 + 间距
    let panelLeft = targetRect.right - scrollRect.left + gap

    // 如果面板超出右边界，放到选区左侧
    if (panelLeft + panelWidth > viewportWidth - 20) {
      panelLeft = targetRect.left - scrollRect.left - panelWidth - gap
    }

    // 如果左侧也放不下（屏幕太窄），使用默认右侧位置
    if (panelLeft < 20) {
      panelLeft = targetRect.right - scrollRect.left + gap
    }

    // 计算面板顶部位置：第一行顶部
    let panelTop = targetRect.top - scrollRect.top - 20

    // 确保不超出底部边界
    if (panelTop + panelHeight > scrollRect.height - 20) {
      panelTop = Math.max(20, scrollRect.height - panelHeight - 20)
    }

    // 确保不超出顶部边界
    if (panelTop < 20) {
      panelTop = 20
    }

    panelPosition.value = {
      top: panelTop,
      left: panelLeft,
    }

    showQAPanel.value = true
  }
}

function closeQAPanel() {
  showQAPanel.value = false
  selectedText.value = ''
  window.getSelection()?.removeAllRanges()
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
        <el-button :icon="isDarkMode ? Sunny : Moon" @click="toggleTheme" text size="small" class="nav-btn"></el-button>
        <el-button :icon="isFocusMode ? Reading : FullScreen" @click="toggleFocusMode" text size="small" class="nav-btn"></el-button>
      </div>
    </nav>

    <div class="sidebar-trigger" v-if="!isFocusMode && hasDocument" @mouseenter="sidebarHovered = true" @mouseleave="sidebarHovered = false">
      <div class="trigger-bar"></div>
    </div>
    
    <LeftSidebar 
      v-if="!isFocusMode && hasDocument" 
      :session-id="sessionId" 
      :class="{ 'is-visible': sidebarHovered }"
      @mouseenter="sidebarHovered = true"
      @mouseleave="sidebarHovered = false"
    />

    <div class="page-shell">
      <div class="scroll-container" ref="scrollContainerRef">
        <DocumentUploader 
          v-if="!hasDocument && !parsing" 
          @uploaded="handleUpload" 
        />
        
        <ParsingProgress 
          v-else-if="parsing" 
          :progress="parseProgress" 
          :stage="parseStage" 
          :content="displayContent" 
        />
        
        <div v-else class="content-wrapper">
          <main class="main-column" ref="contentRef">
            <div class="doc-header">
              <span class="doc-title">{{ documentTitle }}</span>
            </div>
            
            <div class="breadcrumb-bar" :class="{ 'is-visible': showBreadcrumb && currentChapter }">
              <span class="breadcrumb-text">{{ currentChapter }}</span>
            </div>
            
            <div class="markdown-content">
              <FormulaRenderer 
                :content="documentStore.rawMarkdown" 
                @select="handleSelection"
              />
              <div v-if="!documentStore.rawMarkdown && !loading" class="empty-content">
                文档内容为空
              </div>
            </div>
          </main>
          
          <aside class="qa-column">
            <transition name="panel-fade" mode="out-in">
              <QAPanel 
                v-if="showQAPanel && panelPosition" 
                :selected-text="selectedText"
                :session-id="sessionId"
                :position="panelPosition"
                @close="closeQAPanel"
              />
            </transition>
            <div class="history-wrapper" :class="{ 'is-dimmed': showQAPanel }">
              <QAHistory :messages="qaMessages" />
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
}

.nav-left, .nav-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-title {
  font-size: var(--font-size-base);
  font-weight: 600;
  color: var(--text-primary);
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

.content-wrapper {
  display: flex;
  min-height: calc(100vh - 48px);
}

.main-column {
  flex: 1;
  min-width: 600px;
  padding: 0 8vw;
  transition: padding var(--transition-normal);
}

.maphiver-app.is-focus-mode .main-column {
  padding: 0 15vw;
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

.empty-content {
  text-align: center;
  color: var(--text-secondary);
  padding: 100px 0;
}

.qa-column {
  width: 400px;
  padding: 16px;
  padding-left: 0;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.history-wrapper {
  transition: opacity 0.4s ease, filter 0.4s ease;
}

.history-wrapper.is-dimmed {
  opacity: 0.3;
  filter: blur(1px);
  pointer-events: none;
}

/* 面板进入动画 */
.panel-fade-enter-active,
.panel-fade-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.panel-fade-enter-from,
.panel-fade-leave-to {
  opacity: 0;
  transform: translateX(20px) scale(0.98);
}
</style>