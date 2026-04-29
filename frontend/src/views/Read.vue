<script setup lang="ts">
import { ref, onMounted, computed, nextTick, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore, useDocumentStore } from '@/stores'
import { ElMessage, ElButton, ElDialog, ElInput } from 'element-plus'
import { ArrowLeft, Sunny, Moon, FullScreen, Reading, Edit } from '@element-plus/icons-vue'
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

// 暂停控制
const isPaused = computed(() => documentStore.isPaused)

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
const sessionName = computed(() => sessionStore.currentSession?.name || '未命名会话')

// 会话名称编辑相关
const showRenameDialog = ref(false)
const editingSessionName = ref('')

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

function openRenameDialog() {
  editingSessionName.value = sessionName.value
  showRenameDialog.value = true
}

async function saveSessionName() {
  if (!editingSessionName.value.trim()) {
    ElMessage.warning('会话名称不能为空')
    return
  }
  try {
    await sessionStore.updateSessionName(sessionId.value, editingSessionName.value.trim())
    ElMessage.success('名称已更新')
    showRenameDialog.value = false
  } catch (error: any) {
    ElMessage.error(error.message || '更新失败')
  }
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
  setupPanelScrollHide()
})

onUnmounted(() => {
  removeScrollObserver()
  removePanelScrollHide()
  if (displayTimer) {
    cancelAnimationFrame(displayTimer)
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

// 滚动时隐藏 QA 面板，避免面板位置与选区脱节
let scrollHandler: (() => void) | null = null

function setupPanelScrollHide() {
  const container = scrollContainerRef.value
  if (container) {
    scrollHandler = () => {
      if (showQAPanel.value) {
        // 页面滚动时隐藏面板，保持用户体验
        closeQAPanel()
      }
    }
    container.addEventListener('scroll', scrollHandler, { passive: true })
  }
}

function removePanelScrollHide() {
  const container = scrollContainerRef.value
  if (container && scrollHandler) {
    container.removeEventListener('scroll', scrollHandler)
    scrollHandler = null
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
  if (displayTimer) cancelAnimationFrame(displayTimer)

  function tick() {
    if (streamBuffer.length > 0) {
      const chunkSize = Math.max(1, Math.ceil(streamBuffer.length * 0.3))
      displayContent.value += streamBuffer.slice(0, chunkSize)
      streamBuffer = streamBuffer.slice(chunkSize)
    }

    if (streamBuffer.length > 0 || parsing.value) {
      displayTimer = requestAnimationFrame(tick)
    } else {
      displayTimer = null
    }
  }

  displayTimer = requestAnimationFrame(tick)
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

  if (targetRect && targetRect.width > 0 && targetRect.height > 0) {
    const panelHeight = 500 // 预估面板高度
    const viewportHeight = window.innerHeight

    // 水平位置固定在窗口右侧（距右边界 20px）
    // 竖直方向动态跟随选区
    let panelTop = targetRect.top - 10 // 稍微对齐选区顶部

    // 底部边界检测：确保面板在窗口高度范围内
    if (panelTop + panelHeight > viewportHeight - 20) {
      panelTop = Math.max(60, viewportHeight - panelHeight - 60)
    }

    // 顶部边界检测
    if (panelTop < 60) {
      panelTop = 60
    }

    panelPosition.value = {
      top: panelTop,
      right: 20, // 固定在右侧
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

// 暂停格式化显示
function handlePauseParsing() {
  documentStore.pauseParsing()
}

// 继续格式化显示
function handleResumeParsing() {
  documentStore.resumeParsing()
}

// 停止格式化
function handleStopParsing() {
  documentStore.stopParsing()
  parsing.value = false
  ElMessage.warning('格式化已停止')
}
</script>

<template>
  <div class="maphiver-app" :class="{ 'is-focus-mode': isFocusMode }" v-loading="loading && !parsing">
    <nav class="top-nav">
      <div class="nav-left">
        <el-button :icon="ArrowLeft" @click="goBack" text size="small" class="nav-btn" v-if="!isFocusMode"></el-button>
      </div>
      <div class="nav-center" v-if="hasDocument && !isFocusMode">
        <div class="nav-session-name" @click="openRenameDialog">
          <span>{{ sessionName }}</span>
          <el-icon class="edit-icon"><Edit /></el-icon>
        </div>
      </div>
      <div class="nav-right">
        <el-button :icon="isDarkMode ? Sunny : Moon" @click="toggleTheme" text size="small" class="nav-btn"></el-button>
        <el-button :icon="isFocusMode ? Reading : FullScreen" @click="toggleFocusMode" text size="small" class="nav-btn"></el-button>
      </div>
    </nav>

    <!-- 会话名称编辑对话框 -->
    <ElDialog
      v-model="showRenameDialog"
      title="编辑会话名称"
      width="400px"
      :close-on-click-modal="false"
    >
      <ElInput
        v-model="editingSessionName"
        placeholder="输入会话名称"
        maxlength="50"
        show-word-limit
      />
      <template #footer>
        <ElButton @click="showRenameDialog = false">取消</ElButton>
        <ElButton type="primary" @click="saveSessionName">保存</ElButton>
      </template>
    </ElDialog>

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
          :isPaused="isPaused"
          @pause="handlePauseParsing"
          @resume="handleResumeParsing"
          @stop="handleStopParsing"
        />
        
        <div v-else class="content-wrapper">
          <main class="main-column" ref="contentRef">
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
  font-family: var(--font-serif);
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
  min-width: 100px;
}

.nav-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-session-name {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 6px;
  transition: all 0.2s ease;
  max-width: 400px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-session-name:hover {
  color: var(--text-accent);
  background: var(--bg-hover);
}

.nav-session-name .edit-icon {
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.nav-session-name:hover .edit-icon {
  opacity: 1;
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