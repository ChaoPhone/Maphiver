<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElButton, ElIcon } from 'element-plus'
import { ChatDotRound, EditPen, Close } from '@element-plus/icons-vue'
import FormulaRenderer from './FormulaRenderer.vue'
import * as api from '@/api'

const props = defineProps<{
  selectedText: string
  sessionId: string
  position: { top: number; right: number }
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'card-created'): void
}>()

const question = ref('')
const answering = ref(false)
const streamingAnswer = ref('')
const showCardInput = ref(false)
const cardAnnotation = ref('')
const cardCreating = ref(false)
const cardSuccess = ref(false)

const quickQuestions = [
  { type: 'explain', label: '解释', template: '请解释这段内容' },
  { type: 'summary', label: '总结', template: '请总结这段内容的核心要点' },
  { type: 'example', label: '举例', template: '请举例说明这个概念' },
  { type: 'solve', label: '解题', template: '请给出这道题的详细解答步骤' },
]

async function askQuestion(qType?: string) {
  if (!props.selectedText) {
    ElMessage.warning('请先选中文字')
    return
  }
  
  const actualQuestion = qType 
    ? quickQuestions.find(q => q.type === qType)?.template || '请解释这段内容'
    : question.value || '请解释这段内容'
  
  answering.value = true
  streamingAnswer.value = ''
  
  try {
    await api.askQuestionStream(
      props.sessionId,
      actualQuestion,
      props.selectedText,
      undefined,
      (chunk: any) => {
        if (chunk.type === 'text') {
          streamingAnswer.value += chunk.content || ''
        }
      }
    )
    question.value = ''
  } catch (error: any) {
    ElMessage.error(error.message || '提问失败')
  }
  
  answering.value = false
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
  if (!props.selectedText || !props.sessionId) return
  
  cardCreating.value = true
  try {
    await api.createCard(props.sessionId, props.selectedText, cardAnnotation.value)
    cardSuccess.value = true
    emit('card-created')
    
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
  if (!props.selectedText || !props.sessionId) return
  
  try {
    await api.createCard(props.sessionId, props.selectedText)
    ElMessage.success('已摘录为知识卡片')
    emit('card-created')
    emit('close')
  } catch (error: any) {
    ElMessage.error(error.message || '创建卡片失败')
  }
}
</script>

<template>
  <div v-if="position" class="qa-panel" :style="{ top: (position.top || 0) + 'px', left: (position.left || 0) + 'px' }">
    <div class="panel-header">
      <span class="panel-label">已选中 {{ selectedText.length }} 字</span>
      <el-button size="small" text :icon="Close" @click="emit('close')" />
    </div>
    
    <div class="panel-context">
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
      <FormulaRenderer :content="streamingAnswer" />
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
</template>

<style scoped>
.qa-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 20px;
  position: absolute;
  left: 0;
  width: 380px;
  z-index: 100;
  box-shadow: var(--shadow-md);
  max-height: 80vh;
  min-height: 200px;
  overflow-y: auto;
  overflow-x: hidden;
  transition: top 0.3s cubic-bezier(0.4, 0, 0.2, 1), left 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.qa-panel::-webkit-scrollbar {
  width: 6px;
}

.qa-panel::-webkit-scrollbar-track {
  background: transparent;
}

.qa-panel::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.qa-panel::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.panel-label {
  font-size: var(--font-size-base);
  color: var(--text-accent);
  font-weight: 600;
}

.panel-context {
  margin-bottom: 16px;
}

.context-quote {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
  background: var(--bg-hover);
  padding: 12px 16px;
  border-radius: 8px;
  display: block;
  line-height: 1.6;
  border-left: 3px solid var(--text-accent);
}

.quick-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.question-composer {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.question-input {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: var(--font-size-base);
  background: var(--bg-main);
  color: var(--text-primary);
  transition: all 0.2s;
}

.question-input:focus {
  outline: none;
  border-color: var(--text-accent);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--text-accent) 20%, transparent);
}

.card-input-area {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
}

.annotation-input {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: var(--font-size-base);
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
  gap: 10px;
  color: var(--success-color);
  font-weight: 500;
}

.card-input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.stream-area {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
}

.stream-label {
  font-size: var(--font-size-base);
  color: var(--text-primary);
  margin-bottom: 12px;
  font-weight: 600;
}

.stream-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-accent);
  margin-top: 12px;
  font-size: var(--font-size-sm);
}

.stream-actions {
  margin-top: 16px;
}

.panel-actions {
  display: flex;
  justify-content: flex-end;
}
</style>