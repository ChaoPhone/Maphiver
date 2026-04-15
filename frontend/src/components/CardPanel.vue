<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Notebook, Plus, Edit, Delete } from '@element-plus/icons-vue'
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
  <el-card class="card-panel" v-loading="loading">
    <template #header>
      <div class="panel-header">
        <el-icon><Notebook /></el-icon>
        <span>知识卡片</span>
        <el-tag size="small" type="info">{{ cardCount }} 张</el-tag>
      </div>
    </template>
    
    <div v-if="hasSelection" class="selection-area">
      <el-tag closable @close="emit('clear-selection')" type="success">
        已选中 {{ selectedText.length }} 字
      </el-tag>
      <div class="selection-preview">{{ selectedText.slice(0, 80) }}...</div>
      <el-button 
        :icon="Plus" 
        type="primary" 
        size="small"
        @click="openCreateDialog"
      >
        摘录为卡片
      </el-button>
    </div>
    
    <el-scrollbar height="200px" class="cards-list">
      <div v-if="cards.length === 0" class="empty-cards">
        <p>暂无知识卡片</p>
        <p class="hint">选中文本后点击"摘录"按钮创建</p>
      </div>
      
      <div v-for="card in cards" :key="card.id" class="card-item">
        <div class="card-source">{{ card.source_text.slice(0, 100) }}...</div>
        <div v-if="card.annotation" class="card-annotation">
          <span class="annotation-label">批注:</span>
          {{ card.annotation }}
        </div>
        <div class="card-meta">
          <span class="card-time">{{ formatDate(card.created_at) }}</span>
          <div class="card-actions">
            <el-button 
              :icon="Edit" 
              size="small" 
              text
              @click="openEditDialog(card)"
            />
            <el-button 
              :icon="Delete" 
              size="small" 
              text
              type="danger"
              @click="deleteCard(card)"
            />
          </div>
        </div>
      </div>
    </el-scrollbar>
    
    <el-dialog
      v-model="showCreateDialog"
      title="创建知识卡片"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="create-dialog-content">
        <div class="source-preview">
          <div class="source-label">摘录内容:</div>
          <div class="source-text">{{ selectedText.slice(0, 200) }}{{ selectedText.length > 200 ? '...' : '' }}</div>
        </div>
        <el-input
          v-model="annotation"
          type="textarea"
          :rows="3"
          placeholder="添加批注（可选）"
        />
      </div>
      <template #footer>
        <el-button @click="closeCreateDialog">取消</el-button>
        <el-button type="primary" @click="createCard" :loading="loading">保存</el-button>
      </template>
    </el-dialog>
    
    <el-dialog
      v-model="showEditDialog"
      title="编辑批注"
      width="400px"
      :close-on-click-modal="false"
    >
      <div class="edit-dialog-content">
        <div class="source-preview">
          <div class="source-label">原文:</div>
          <div class="source-text">{{ editingCard?.source_text?.slice(0, 150) }}...</div>
        </div>
        <el-input
          v-model="editAnnotation"
          type="textarea"
          :rows="3"
          placeholder="修改批注内容"
        />
      </div>
      <template #footer>
        <el-button @click="closeEditDialog">取消</el-button>
        <el-button type="primary" @click="updateCard" :loading="loading">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<style scoped>
.card-panel {
  height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.selection-area {
  padding: 10px;
  background: #f0f9eb;
  border-radius: 8px;
  margin-bottom: 15px;
}

.selection-preview {
  font-size: 12px;
  color: #67c23a;
  margin: 8px 0;
  padding: 5px;
  background: #fff;
  border-radius: 4px;
}

.cards-list {
  margin-top: 10px;
}

.empty-cards {
  text-align: center;
  padding: 20px;
  color: #909399;
}

.empty-cards .hint {
  font-size: 12px;
  color: #c0c4cc;
}

.card-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 10px;
}

.card-source {
  color: #303133;
  line-height: 1.5;
  font-size: 13px;
}

.card-annotation {
  margin-top: 8px;
  padding: 8px;
  background: #ecf5ff;
  border-radius: 4px;
  font-size: 12px;
  color: #409eff;
}

.annotation-label {
  font-weight: 500;
  margin-right: 4px;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.card-time {
  font-size: 12px;
  color: #909399;
}

.card-actions {
  display: flex;
  gap: 4px;
}

.create-dialog-content,
.edit-dialog-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.source-preview {
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.source-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.source-text {
  color: #303133;
  line-height: 1.5;
}
</style>