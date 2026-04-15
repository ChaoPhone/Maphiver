<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Clock, ChatDotRound, Document, Reading, EditPen, QuestionFilled } from '@element-plus/icons-vue'
import type { Footprint } from '@/types'
import * as api from '@/api'

const props = defineProps<{
  sessionId: string
}>()

const footprints = ref<Footprint[]>([])
const loading = ref(false)

const actionTypeMap: Record<string, { label: string; icon: any; color: string }> = {
  'qa_ask': { label: '提问', icon: QuestionFilled, color: '#409eff' },
  'qa_answer': { label: '回答', icon: ChatDotRound, color: '#67c23a' },
  'card_create': { label: '摘录', icon: EditPen, color: '#e6a23c' },
  'card_edit': { label: '编辑批注', icon: EditPen, color: '#909399' },
  'card_delete': { label: '删除卡片', icon: EditPen, color: '#f56c6c' },
  'session_start': { label: '开始阅读', icon: Reading, color: '#409eff' },
  'session_end': { label: '结束阅读', icon: Document, color: '#909399' },
}

const footprintCount = computed(() => footprints.value.length)

const groupedFootprints = computed(() => {
  const groups: Record<string, Footprint[]> = {}
  footprints.value.forEach(fp => {
    const date = new Date(fp.created_at).toLocaleDateString('zh-CN')
    if (!groups[date]) groups[date] = []
    groups[date].push(fp)
  })
  return Object.entries(groups).reverse()
})

async function loadFootprints() {
  if (!props.sessionId) return
  loading.value = true
  try {
    footprints.value = await api.getFootprints(props.sessionId)
  } catch (error: any) {
    ElMessage.error('加载足迹失败: ' + error.message)
  }
  loading.value = false
}

watch(() => props.sessionId, () => {
  loadFootprints()
}, { immediate: true })

function getActionInfo(actionType: string) {
  return actionTypeMap[actionType] || { label: actionType, icon: Clock, color: '#909399' }
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function getContextPreview(context: Record<string, any> | undefined): string {
  if (!context) return ''
  if (context.question) return context.question.slice(0, 50) + '...'
  if (context.source_text) return context.source_text.slice(0, 50) + '...'
  return ''
}
</script>

<template>
  <el-card class="footprint-panel" v-loading="loading">
    <template #header>
      <div class="panel-header">
        <el-icon><Clock /></el-icon>
        <span>学习足迹</span>
        <el-tag size="small" type="info">{{ footprintCount }} 条</el-tag>
      </div>
    </template>

    <el-scrollbar height="300px" class="footprint-list">
      <div v-if="footprints.length === 0" class="empty-footprints">
        <p>暂无学习足迹</p>
        <p class="hint">阅读、问答、摘录都会记录在这里</p>
      </div>

      <div v-for="[date, items] in groupedFootprints" :key="date" class="footprint-group">
        <div class="group-date">{{ date }}</div>
        <div class="timeline">
          <div v-for="fp in items" :key="fp.id" class="timeline-item">
            <div class="timeline-marker" :style="{ backgroundColor: getActionInfo(fp.action_type).color }">
              <el-icon :size="12">
                <component :is="getActionInfo(fp.action_type).icon" />
              </el-icon>
            </div>
            <div class="timeline-content">
              <div class="action-label">{{ getActionInfo(fp.action_type).label }}</div>
              <div class="action-time">{{ formatTime(fp.created_at) }}</div>
              <div v-if="getContextPreview(fp.context)" class="action-context">
                {{ getContextPreview(fp.context) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-scrollbar>
  </el-card>
</template>

<style scoped>
.footprint-panel {
  height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.footprint-list {
  padding-right: 10px;
}

.empty-footprints {
  text-align: center;
  color: #909399;
  padding: 20px;
}

.empty-footprints .hint {
  font-size: 12px;
  margin-top: 5px;
}

.footprint-group {
  margin-bottom: 15px;
}

.group-date {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  padding-left: 5px;
}

.timeline {
  position: relative;
  padding-left: 20px;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e4e7ed;
}

.timeline-item {
  position: relative;
  padding-bottom: 12px;
  display: flex;
  align-items: flex-start;
}

.timeline-marker {
  position: absolute;
  left: -20px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  z-index: 1;
}

.timeline-content {
  flex: 1;
  min-width: 0;
}

.action-label {
  font-size: 14px;
  color: #303133;
}

.action-time {
  font-size: 12px;
  color: #909399;
}

.action-context {
  font-size: 12px;
  color: #606266;
  margin-top: 4px;
  padding: 4px 8px;
  background: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>