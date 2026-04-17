<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Notebook, Plus, Edit, Delete, Document, ChatLineSquare } from '@element-plus/icons-vue'
import type { KnowledgeCard } from '@/types'
import * as api from '@/api'

const props = defineProps<{
  sessionId: string
  selectedText: string
}>()

const emit = defineEmits<{
  (e: 'clear-selection'): void
}>()

const cards = ref<KnowledgeCard[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const editingCard = ref<KnowledgeCard | null>(null)
const annotation = ref('')
const editAnnotation = ref('')

const hasSelection = computed(() => props.selectedText.trim().length > 0)
const cardCount = computed(() => cards.value.length)

async function loadCards() {
  if (!props.sessionId) return
  loading.value = true
  try {
    cards.value = await api.getCards(props.sessionId)
  } catch (error: any) {
    ElMessage.error('加载卡片失败: ' + error.message)
  }
  loading.value = false
}

watch(() => props.sessionId, () => {
  loadCards()
}, { immediate: true })

function openCreateDialog() {
  if (!hasSelection.value) {
    ElMessage.warning('请先选中要摘录的文本')
    return
  }
  annotation.value = ''
  showCreateDialog.value = true
}

function closeCreateDialog() {
  showCreateDialog.value = false
  annotation.value = ''
}

async function createCard() {
  if (!props.selectedText.trim()) {
    ElMessage.warning('摘录内容不能为空')
    return
  }
  
  loading.value = true
  try {
    await api.createCard(
      props.sessionId,
      props.selectedText,
      annotation.value || undefined
    )
    ElMessage.success('摘录成功')
    closeCreateDialog()
    emit('clear-selection')
    await loadCards()
  } catch (error: any) {
    ElMessage.error('创建失败: ' + error.message)
  }
  loading.value = false
}

function openEditDialog(card: KnowledgeCard) {
  editingCard.value = card
  editAnnotation.value = card.annotation || ''
  showEditDialog.value = true
}

function closeEditDialog() {
  showEditDialog.value = false
  editingCard.value = null
  editAnnotation.value = ''
}

async function updateCard() {
  if (!editingCard.value) return
  
  loading.value = true
  try {
    await api.updateCard(editingCard.value.id, editAnnotation.value)
    ElMessage.success('批注已更新')
    closeEditDialog()
    await loadCards()
  } catch (error: any) {
    ElMessage.error('更新失败: ' + error.message)
  }
  loading.value = false
}

async function deleteCard(card: KnowledgeCard) {
  try {
    await ElMessageBox.confirm(
      '确定删除这张知识卡片？',
      '删除确认',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
    
    await api.deleteCard(card.id)
    ElMessage.success('卡片已删除')
    await loadCards()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <el-card class="study-card-panel" v-loading="loading" shadow="never">
    <template #header>
      <div class="panel-header">
        <div class="header-title">
          <el-icon class="header-icon"><Notebook /></el-icon>
          <span>知识闪卡</span>
        </div>
        <span class="card-count">{{ cardCount }} 张</span>
      </div>
    </template>
    
    <!-- 沉浸式选词区 -->
    <transition name="fade-slide">
      <div v-if="hasSelection" class="selection-area">
        <div class="selection-header">
          <span class="selection-label">正在摘录</span>
          <el-button link type="info" size="small" @click="emit('clear-selection')">取消</el-button>
        </div>
        <div class="selection-preview">{{ selectedText.slice(0, 100) }}{{ selectedText.length > 100 ? '...' : '' }}</div>
        <div class="selection-actions">
          <span class="word-count">{{ selectedText.length }} 字</span>
          <el-button 
            :icon="Plus" 
            class="capture-btn"
            size="small"
            @click="openCreateDialog"
          >
            保存为卡片
          </el-button>
        </div>
      </div>
    </transition>
    
    <el-scrollbar height="100%" class="cards-list">
      <div v-if="cards.length === 0" class="empty-state">
        <el-icon class="empty-icon"><Document /></el-icon>
        <p>你的知识库还是空的</p>
        <p class="hint">在阅读时选中文本，即可开始沉淀知识</p>
      </div>
      
      <div v-for="card in cards" :key="card.id" class="knowledge-card">
        <!-- 原文区 -->
        <div class="card-source">
          {{ card.source_text }}
        </div>
        
        <!-- 批注区 -->
        <div v-if="card.annotation" class="card-annotation">
          <el-icon class="annotation-icon"><ChatLineSquare /></el-icon>
          <div class="annotation-content">{{ card.annotation }}</div>
        </div>
        
        <!-- 元数据与操作区 -->
        <div class="card-footer">
          <span class="card-time">{{ formatDate(card.created_at) }}</span>
          <div class="card-actions">
            <el-button 
              :icon="Edit" 
              size="small" 
              link
              class="action-btn"
              @click="openEditDialog(card)"
            />
            <el-button 
              :icon="Delete" 
              size="small" 
              link
              class="action-btn delete-btn"
              @click="deleteCard(card)"
            />
          </div>
        </div>
      </div>
    </el-scrollbar>
    
    <!-- 极简风格的弹窗 -->
    <el-dialog
      v-model="showCreateDialog"
      title="记录你的思考"
      width="450px"
      :close-on-click-modal="false"
      class="study-dialog"
    >
      <div class="dialog-content">
        <div class="quote-preview">
          {{ selectedText.slice(0, 200) }}{{ selectedText.length > 200 ? '...' : '' }}
        </div>
        <el-input
          v-model="annotation"
          type="textarea"
          :rows="4"
          placeholder="写下你对此处内容的感悟或批注（选填）..."
          class="study-textarea"
        />
      </div>
      <template #footer>
        <el-button @click="closeCreateDialog" plain>取消</el-button>
        <el-button color="#303133" @click="createCard" :loading="loading">存入卡片</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showEditDialog"
      title="修改批注"
      width="450px"
      :close-on-click-modal="false"
      class="study-dialog"
    >
      <div class="dialog-content">
        <div class="quote-preview">
          {{ editingCard?.source_text?.slice(0, 150) }}...
        </div>
        <el-input
          v-model="editAnnotation"
          type="textarea"
          :rows="4"
          placeholder="修改你的批注..."
          class="study-textarea"
        />
      </div>
      <template #footer>
        <el-button @click="closeEditDialog" plain>取消</el-button>
        <el-button color="#303133" @click="updateCard" :loading="loading">保存修改</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<style scoped>
/* 容器基础样式 */
.study-card-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  border: none;
  border-right: 1px solid #ebeef5; /* 如果作为侧边栏，可以用极细的边框代替阴影 */
  border-radius: 0;
  background-color: #fafafa;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  background-color: #fff;
}

:deep(.el-card__body) {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background-color: #fafafa;
}

/* 头部样式 */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.header-icon {
  font-size: 18px;
  color: #606266;
}

.card-count {
  font-size: 12px;
  color: #909399;
  background: #f4f4f5;
  padding: 2px 8px;
  border-radius: 10px;
}

/* 选区卡片 (Action Sheet 风格) */
.selection-area {
  background: #ffffff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  position: relative;
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.selection-label {
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.selection-preview {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 12px;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.selection-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px dashed #ebeef5;
  padding-top: 12px;
}

.word-count {
  font-size: 12px;
  color: #c0c4cc;
}

.capture-btn {
  background-color: #303133;
  color: #fff;
  border: none;
  border-radius: 6px;
  transition: opacity 0.2s;
}
.capture-btn:hover {
  background-color: #4a4a4a;
  color: #fff;
}

/* 列表容器 */
.cards-list {
  flex: 1;
  margin-right: -10px; /* 为滚动条留白 */
  padding-right: 10px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon {
  font-size: 48px;
  color: #dcdfe6;
  margin-bottom: 16px;
}

.empty-state p {
  margin: 4px 0;
  font-size: 14px;
}

.empty-state .hint {
  font-size: 12px;
  color: #c0c4cc;
}

/* 知识卡片主体 */
.knowledge-card {
  background: #ffffff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.knowledge-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
  border-color: #dcdfe6;
}

/* 原文样式 (带左侧引用线) */
.card-source {
  color: #4a4a4a;
  line-height: 1.7;
  font-size: 14px;
  position: relative;
  padding-left: 14px;
  margin-bottom: 12px;
}

.card-source::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 3px;
  background-color: #dcdfe6;
  border-radius: 2px;
}

/* 批注样式 (仿便签暖色背景) */
.card-annotation {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px;
  background: #fdfcf8; /* 极淡的暖黄色 */
  border: 1px solid #f4f1e1;
  border-radius: 6px;
  margin-top: 12px;
}

.annotation-icon {
  color: #e6a23c;
  font-size: 14px;
  margin-top: 2px;
}

.annotation-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

/* 卡片底部操作区 */
.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #f5f7fa;
}

.card-time {
  font-size: 12px;
  color: #c0c4cc;
}

.card-actions {
  display: flex;
  gap: 4px;
  opacity: 0; /* 默认隐藏，降低干扰 */
  transition: opacity 0.2s;
}

.knowledge-card:hover .card-actions {
  opacity: 1; /* 悬浮时展示 */
}

.action-btn {
  color: #909399;
}

.action-btn:hover {
  color: #409eff;
  background: #f4f4f5;
}

.delete-btn:hover {
  color: #f56c6c;
}

/* 弹窗内的沉浸式输入设计 */
.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quote-preview {
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  font-style: italic;
}

:deep(.study-textarea .el-textarea__inner) {
  background-color: #ffffff;
  border: 1px solid #dcdfe6;
  box-shadow: none;
  font-size: 14px;
  line-height: 1.6;
  padding: 12px;
  resize: none;
}

:deep(.study-textarea .el-textarea__inner:focus) {
  border-color: #909399;
}

/* 动画效果 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>