<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentStore, useSessionStore } from '@/stores'
import { ElMessage, ElButton, ElInput, ElMessageBox, ElCheckbox } from 'element-plus'
import { Search, Delete, Star, Top, More } from '@element-plus/icons-vue'
import DocumentUploader from '@/components/DocumentUploader.vue'
import type { Session, Document as DocType } from '@/types'

const router = useRouter()
const documentStore = useDocumentStore()
const sessionStore = useSessionStore()

const loading = ref(false)
const searchQuery = ref('')
const showRenameDialog = ref(false)
const renamingSession = ref<Session | null>(null)
const newName = ref('')
const selectedSessions = ref<string[]>([])
const showSessionMenu = ref<string | null>(null)

const filteredSessions = computed(() => {
  let sessions = sessionStore.sessions
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    sessions = sessions.filter(s => {
      const docName = s.document?.filename?.toLowerCase() || ''
      const sessionName = s.name?.toLowerCase() || ''
      return docName.includes(query) || sessionName.includes(query)
    })
  }
  return sessions
})

// 滑动区域最大高度（可容纳约一页半内容）
// 会话区 50vh，文档区 40vh

function getSessionDisplayName(session: Session): string {
  return session.name || formatDateTime(session.created_at)
}

function getDocName(session: Session): string {
  return session.document?.filename || '未知文档'
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(async () => {
  loading.value = true
  try {
    await documentStore.fetchDocuments()
    await sessionStore.fetchSessions()
  } catch (error) {
    ElMessage.error('加载失败')
  }
  loading.value = false
})

async function handleUpload(documentId: string, sessionId: string) {
  router.push(`/read/${sessionId}`)
}

async function startReading(documentId: string) {
  try {
    const session = await sessionStore.createSession(documentId)
    router.push(`/read/${session.id}`)
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}

function continueReading(sessionId: string) {
  router.push(`/read/${sessionId}`)
}

async function deleteDocument(doc: DocType) {
  try {
    await ElMessageBox.confirm(
      `确定删除文档 "${doc.filename}" 及其所有阅读会话？`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )

    await documentStore.deleteDocument(doc.id)
    ElMessage.success('文档已删除')
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

async function deleteSession(session: Session) {
  try {
    await ElMessageBox.confirm(
      `确定删除会话 "${getSessionDisplayName(session)}"？`,
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )

    await sessionStore.deleteSession(session.id)
    ElMessage.success('会话已删除')
    selectedSessions.value = selectedSessions.value.filter(id => id !== session.id)
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

async function deleteSelectedSessions() {
  if (selectedSessions.value.length === 0) return

  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${selectedSessions.value.length} 个会话？`,
      '批量删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )

    for (const id of selectedSessions.value) {
      await sessionStore.deleteSession(id)
    }
    ElMessage.success(`已删除 ${selectedSessions.value.length} 个会话`)
    selectedSessions.value = []
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

function openRenameDialog(session: Session) {
  renamingSession.value = session
  newName.value = session.name || ''
  showRenameDialog.value = true
  showSessionMenu.value = null
}

async function saveRename() {
  if (!renamingSession.value) return

  try {
    await sessionStore.updateSessionName(renamingSession.value.id, newName.value)
    ElMessage.success('名称已更新')
    showRenameDialog.value = false
    renamingSession.value = null
    newName.value = ''
  } catch (error: any) {
    ElMessage.error(error.message || '更新失败')
  }
}

async function togglePin(session: Session) {
  try {
    await sessionStore.pinStarSession(session.id, !session.is_pinned, undefined)
    ElMessage.success(session.is_pinned ? '已取消置顶' : '已置顶')
    showSessionMenu.value = null
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

async function toggleStar(session: Session) {
  try {
    await sessionStore.pinStarSession(session.id, undefined, !session.is_starred)
    ElMessage.success(session.is_starred ? '已取消收藏' : '已收藏')
    showSessionMenu.value = null
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
}

function toggleSelectAll() {
  if (selectedSessions.value.length === filteredSessions.value.length) {
    selectedSessions.value = []
  } else {
    selectedSessions.value = filteredSessions.value.map(s => s.id)
  }
}

function toggleSelect(sessionId: string) {
  const index = selectedSessions.value.indexOf(sessionId)
  if (index > -1) {
    selectedSessions.value.splice(index, 1)
  } else {
    selectedSessions.value.push(sessionId)
  }
}

function toggleSessionMenu(sessionId: string) {
  showSessionMenu.value = showSessionMenu.value === sessionId ? null : sessionId
}
</script>

<template>
  <div class="home-container">
    <header class="home-header">
      <h1>流式知识河</h1>
    </header>

    <main class="home-main" v-loading="loading">
      <!-- 上传区域 -->
      <section class="upload-section">
        <DocumentUploader @uploaded="handleUpload" />
      </section>

      <!-- 阅读会话区域 -->
      <section class="session-section">
        <div class="section-header">
          <div class="section-title">
            <span>阅读会话</span>
            <span class="session-count">{{ filteredSessions.length }} 个会话</span>
          </div>
          <div class="section-actions">
            <ElInput
              v-model="searchQuery"
              placeholder="搜索会话..."
              :prefix-icon="Search"
              size="small"
              clearable
              class="search-input"
            />
            <transition name="fade">
              <ElButton
                v-if="selectedSessions.length > 0"
                type="danger"
                size="small"
                @click="deleteSelectedSessions"
              >
                删除 ({{ selectedSessions.length }})
              </ElButton>
            </transition>
          </div>
        </div>

        <div class="session-scroll-area">
            <div
              v-for="session in filteredSessions"
              :key="session.id"
              class="session-item"
              :class="{
                'is-pinned': session.is_pinned,
                'is-starred': session.is_starred,
                'is-selected': selectedSessions.includes(session.id)
              }"
            >
              <div class="session-checkbox">
                <ElCheckbox
                  :model-value="selectedSessions.includes(session.id)"
                  @change="toggleSelect(session.id)"
                />
              </div>

              <div class="session-pin" @click.stop="togglePin(session)">
                <el-icon v-if="session.is_pinned" class="pin-icon active"><Top /></el-icon>
                <el-icon v-else class="pin-icon"><Top /></el-icon>
              </div>

              <div class="session-content" @click="continueReading(session.id)">
                <div class="session-name">
                  <el-icon v-if="session.is_starred" class="star-icon"><Star /></el-icon>
                  {{ getSessionDisplayName(session) }}
                </div>
                <div class="session-doc">{{ getDocName(session) }}</div>
              </div>

              <div class="session-time">{{ formatDateTime(session.updated_at) }}</div>

              <div class="session-actions">
                <ElButton size="small" type="primary" @click.stop="continueReading(session.id)">
                  继续
                </ElButton>
                <div class="menu-wrapper">
                  <ElButton size="small" :icon="More" @click.stop="toggleSessionMenu(session.id)" />
                  <transition name="dropdown">
                    <div v-if="showSessionMenu === session.id" class="session-menu" @click.stop>
                      <div class="menu-item" @click="togglePin(session)">
                        <el-icon><Top /></el-icon>
                        {{ session.is_pinned ? '取消置顶' : '置顶' }}
                      </div>
                      <div class="menu-item" @click="toggleStar(session)">
                        <el-icon><Star /></el-icon>
                        {{ session.is_starred ? '取消收藏' : '收藏' }}
                      </div>
                      <div class="menu-item" @click="openRenameDialog(session)">
                        <el-icon><Search /></el-icon>
                        重命名
                      </div>
                      <div class="menu-item danger" @click="deleteSession(session)">
                        <el-icon><Delete /></el-icon>
                        删除
                      </div>
                    </div>
                  </transition>
                </div>
              </div>
            </div>

            <div v-if="filteredSessions.length === 0" class="empty-state">
              <span v-if="searchQuery">没有找到匹配的会话</span>
              <span v-else>暂无阅读会话，上传文档开始阅读</span>
            </div>
          </div>
      </section>

      <!-- 文档列表区域 -->
      <section class="document-section">
        <div class="section-header">
          <div class="section-title">
            <span>文档列表</span>
            <span class="session-count">{{ documentStore.documents.length }} 个文档</span>
          </div>
        </div>

        <div class="document-scroll-area">
            <div v-for="doc in documentStore.documents" :key="doc.id" class="document-item">
              <div class="doc-info">
                <span class="doc-name">{{ doc.filename }}</span>
                <span class="doc-meta">{{ doc.page_count || '?' }} 页</span>
              </div>
              <div class="doc-actions">
                <ElButton size="small" type="primary" @click="startReading(doc.id)">
                  开始阅读
                </ElButton>
                <ElButton size="small" :icon="Delete" @click="deleteDocument(doc)" />
              </div>
            </div>

            <div v-if="documentStore.documents.length === 0" class="empty-state">
              暂无文档
            </div>
          </div>
      </section>
    </main>

    <ElDialog
      v-model="showRenameDialog"
      title="重命名会话"
      width="360px"
      :close-on-click-modal="false"
    >
      <ElInput
        v-model="newName"
        placeholder="输入新名称..."
        style="width: 100%"
      />
      <template #footer>
        <ElButton @click="showRenameDialog = false">取消</ElButton>
        <ElButton type="primary" @click="saveRename">保存</ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.home-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-main);
  overflow: hidden;
  font-family: var(--font-serif);
}

.home-header {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  background: var(--bg-sidebar);
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.home-header h1 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  font-family: var(--font-serif);
}

.home-main {
  flex: 1;
  overflow-y: auto;
  padding: 0;
  font-family: var(--font-serif);
}

/* 上传区域 */
.upload-section {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-light);
}

/* 区域通用 */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 8px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}

.session-count {
  font-size: 13px;
  color: var(--text-muted);
  background: var(--bg-hover);
  padding: 3px 10px;
  border-radius: 10px;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  width: 180px;
}

/* 阅读会话 */
.session-section {
  padding: 0 48px;
  border-bottom: 1px solid var(--border-light);
}

.session-scroll-area {
  max-height: 45vh;
  overflow-y: auto;
  /* 平滑滚动指示 */
  mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    black 5%,
    black 100%
  );
  -webkit-mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    black 5%,
    black 100%
  );
}

.session-scroll-area::-webkit-scrollbar {
  width: 4px;
}

.session-scroll-area::-webkit-scrollbar-track {
  background: transparent;
}

.session-scroll-area::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light);
  transition: background var(--transition-fast);
}

.session-item:last-child {
  border-bottom: none;
}

.session-item:hover {
  background: var(--bg-hover);
}

.session-item.is-pinned {
  background: rgba(185, 28, 28, 0.04);
  border-left: 3px solid var(--text-accent);
  padding-left: 9px;
  margin-left: -12px;
}

.session-checkbox {
  flex-shrink: 0;
}

.session-pin {
  flex-shrink: 0;
  cursor: pointer;
  padding: 4px;
}

.pin-icon {
  color: var(--text-muted);
  font-size: 14px;
  transition: color var(--transition-fast);
}

.pin-icon.active {
  color: var(--text-accent);
}

.session-pin:hover .pin-icon {
  color: var(--text-accent);
}

.session-content {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.session-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.star-icon {
  color: #F59E0B;
  font-size: 15px;
  flex-shrink: 0;
}

.session-doc {
  font-size: 13px;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 4px;
}

.session-time {
  flex-shrink: 0;
  font-size: 13px;
  color: var(--text-muted);
  width: 110px;
  text-align: right;
}

.session-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 操作菜单 */
.menu-wrapper {
  position: relative;
}

.session-menu {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 100;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  padding: 4px 0;
  min-width: 120px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.menu-item:hover {
  background: var(--bg-hover);
}

.menu-item.danger {
  color: var(--error-color);
}

/* 文档列表 */
.document-section {
  padding: 0 48px 20px;
}

.document-scroll-area {
  max-height: 30vh;
  overflow-y: auto;
  mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    black 8%,
    black 100%
  );
  -webkit-mask-image: linear-gradient(
    to bottom,
    transparent 0%,
    black 8%,
    black 100%
  );
}

.document-scroll-area::-webkit-scrollbar {
  width: 3px;
}

.document-scroll-area::-webkit-scrollbar-track {
  background: transparent;
}

.document-scroll-area::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

.document-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-light);
}

.document-item.is-pinned {
  background: rgba(185, 28, 28, 0.04);
  border-left: 3px solid var(--text-accent);
  padding-left: 9px;
  margin-left: -8px;
}

.document-item:last-child {
  border-bottom: none;
}

.doc-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.doc-name {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.doc-meta {
  font-size: 12px;
  color: var(--text-muted);
  flex-shrink: 0;
}

.doc-actions {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 32px 0;
  font-size: 15px;
  color: var(--text-muted);
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* 滚动条 */
.home-main::-webkit-scrollbar {
  width: 6px;
}

.home-main::-webkit-scrollbar-track {
  background: transparent;
}

.home-main::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.home-main::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
