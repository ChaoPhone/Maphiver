<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage, ElIcon } from 'element-plus'
import { ChatDotRound, EditPen } from '@element-plus/icons-vue'
import FormulaRenderer from './FormulaRenderer.vue'
import * as api from '@/api'

const props = defineProps<{
  selectedText: string
  sessionId: string
  position: { top: number; right: number }
  blockId?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'card-created'): void
  (e: 'qa-created'): void
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
      props.blockId,
      (chunk: any) => {
        if (chunk.type === 'text') {
          streamingAnswer.value += chunk.content || ''
        }
      }
    )
    question.value = ''
    emit('qa-created')  // 通知父组件刷新历史记录
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

// 计算阴影位置（只计算top，左右固定）
const shadowStyle1 = computed(() => ({
  top: (props.position?.top || 0) + 6 + 'px'
}))

const shadowStyle2 = computed(() => ({
  top: (props.position?.top || 0) + 12 + 'px'
}))
</script>

<template>
  <div class="qa-panel-wrapper">
    <!-- 错位阴影卡片 - 固定左侧位置 -->
    <div class="qa-panel-shadow" :style="shadowStyle1"></div>
    <div class="qa-panel-shadow second" :style="shadowStyle2"></div>

    <!-- 主卡片 - 固定左侧位置，top动态 -->
    <div v-if="position" class="qa-panel" :style="{ top: (position.top || 0) + 'px' }">
    <!-- 折页关闭按钮 -->
    <div class="fold-corner" @click="emit('close')">
      <div class="fold-paper"></div>
      <div class="fold-x">
        <svg width="12" height="12" viewBox="0 0 12 12">
          <line x1="2" y1="2" x2="10" y2="10" stroke="currentColor" stroke-width="1.5"/>
          <line x1="10" y1="2" x2="2" y2="10" stroke="currentColor" stroke-width="1.5"/>
        </svg>
      </div>
    </div>
    
    <!-- 选中文本 - 引用格式 -->
    <blockquote class="context-quote">
      {{ selectedText.slice(0, 150) }}{{ selectedText.length > 150 ? '...' : '' }}
    </blockquote>
    
    <!-- 快捷问题 - 下划线滑动样式 -->
    <div class="quick-actions">
      <span 
        v-for="q in quickQuestions" 
        :key="q.type"
        class="action-link"
        :class="{ disabled: answering }"
        @click="!answering && askQuestion(q.type)"
      >
        <span class="link-text">{{ q.label }}</span>
        <span class="link-underline"></span>
      </span>
    </div>

    <!-- 自定义问题输入 -->
    <div class="question-composer">
      <div class="input-wrapper" :class="{ focused: question.length > 0 }">
        <input
          v-model="question"
          type="text"
          placeholder="追问..."
          class="question-input"
          @keyup.enter="askQuestion()"
        />
        <span class="input-underline"></span>
      </div>
      <span 
        class="action-link primary"
        :class="{ disabled: answering || !selectedText }"
        @click="!answering && selectedText && askQuestion()"
      >
        <span class="link-text">{{ answering ? '思考中' : '提问' }}</span>
        <span class="link-underline"></span>
      </span>
    </div>
    
    <!-- AI 回复区域 -->
    <div v-if="streamingAnswer" class="stream-area">
      <div class="stream-answer">
        <FormulaRenderer :content="streamingAnswer" />
      </div>
      <div v-if="answering" class="stream-loading">
        <el-icon class="is-loading"><ChatDotRound /></el-icon>
        <span>正在展开...</span>
      </div>
      <div v-if="!answering && streamingAnswer" class="stream-actions">
        <span class="action-link" @click="createCardFromSelection">
          <el-icon><EditPen /></el-icon>
          <span class="link-text">摘录</span>
          <span class="link-underline"></span>
        </span>
      </div>
    </div>
    
    <!-- 摘录卡片入口 - 图标 + hover展开文字 -->
    <div v-else class="excerpt-entry">
      <span class="excerpt-expand" @click="showCardAnnotationInput">
        <el-icon class="excerpt-icon"><EditPen /></el-icon>
        <span class="excerpt-text">摘录为卡片</span>
      </span>
    </div>
    
    <!-- 批注输入 -->
    <div v-if="showCardInput" class="card-input-area">
      <div class="input-wrapper" :class="{ focused: cardAnnotation.length > 0 }">
        <input 
          v-model="cardAnnotation"
          type="text"
          placeholder="添加批注..."
          class="annotation-input"
          @keyup.enter="createCardWithAnnotation"
          @keyup.escape="cancelCardCreation"
          :disabled="cardCreating"
        />
        <span class="input-underline"></span>
      </div>
      <div v-if="cardSuccess" class="card-success">
        已汇入知识河
      </div>
      <div v-else class="card-input-actions">
        <span class="action-link muted" @click="cancelCardCreation">
          <span class="link-text">取消</span>
          <span class="link-underline"></span>
        </span>
        <span 
          class="action-link primary"
          :class="{ disabled: cardCreating }"
          @click="!cardCreating && createCardWithAnnotation()"
        >
          <span class="link-text">{{ cardCreating ? '保存中' : '保存' }}</span>
          <span class="link-underline"></span>
        </span>
      </div>
    </div>
  </div><!-- qa-panel -->
</div><!-- qa-panel-wrapper -->
</template>

<style scoped>
/* 错位阴影卡片 - 固定在右侧 */
.qa-panel-shadow {
  position: fixed;
  left: calc(75vw + 16px);
  right: 26px;
  background: var(--bg-sidebar);
  border-radius: 12px;
  z-index: 999;
  opacity: 0.6;
  pointer-events: none;
  transition: top 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.qa-panel-shadow.second {
  opacity: 0.3;
  z-index: 998;
}

/* 主卡片 - 固定在右侧，左边缘接近75vw */
.qa-panel {
  position: fixed;
  left: calc(75vw + 10px);  /* 左侧接近主文档右边缘 */
  right: 20px;  /* 右边距 */
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 24px;
  padding-top: 32px;
  z-index: 1000;
  max-height: 65vh;
  overflow-y: auto;
  overflow-x: hidden;
  font-family: var(--font-serif);

  /* 渐入渐出动画 */
  animation: panel-enter 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes panel-enter {
  from {
    opacity: 0;
    transform: translateX(20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

/* 离开动画由父组件的 transition 控制 */
.qa-panel::-webkit-scrollbar {
  width: 5px;
}

.qa-panel::-webkit-scrollbar-track {
  background: transparent;
}

.qa-panel::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

/* 折页关闭按钮 - 卷起、变色、显示X */
.fold-corner {
  position: absolute;
  top: 0;
  right: 0;
  width: 36px;
  height: 36px;
  cursor: pointer;
  overflow: visible;
}

.fold-paper {
  position: absolute;
  top: 0;
  right: 0;
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--bg-card) 50%, var(--bg-hover) 50%);
  clip-path: polygon(0 0, 100% 0, 100% 100%);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: top right;
}

.fold-x {
  position: absolute;
  top: 10px;
  right: 10px;
  color: transparent;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* hover: 卷起 + 变主题色 + 显示X */
.fold-corner:hover .fold-paper {
  background: linear-gradient(135deg, var(--bg-card) 50%, var(--text-accent) 50%);
  transform: rotate(-15deg) scale(1.1);
  clip-path: polygon(0 0, 100% 0, 100% 80%, 80% 100%);
}

.fold-corner:hover .fold-x {
  color: var(--text-accent);
  opacity: 1;
  transform: translate(2px, 2px);
}

/* 选中文本 - markdown 引用格式 */
.context-quote {
  margin: 0 0 20px 0;
  padding: 12px 16px;
  border-left: 4px solid var(--text-accent);
  background: var(--bg-note);
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.8;
  font-style: italic;
}

/* 下划线滑动按钮 */
.action-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
  color: var(--text-secondary);
  font-size: 14px;
  font-family: var(--font-serif);
  cursor: pointer;
  position: relative;
  transition: color 0.2s ease;
}

.action-link.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.link-text {
  position: relative;
  z-index: 1;
}

/* 下划线 - 从右向左滑动出现 */
.link-underline {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 1px;
  background: var(--text-accent);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-link:hover:not(.disabled) {
  color: var(--text-accent);
}

.action-link:hover:not(.disabled) .link-underline {
  width: 100%;
}

.action-link.primary {
  color: var(--text-accent);
  font-weight: 500;
}

.action-link.primary .link-underline {
  background: var(--text-accent);
}

.action-link.muted {
  color: var(--text-muted);
}

.action-link.muted .link-underline {
  background: var(--text-secondary);
}

.action-link.muted:hover:not(.disabled) {
  color: var(--text-secondary);
}

/* 快捷问题 */
.quick-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

/* 问题输入 - 下划线滑动 */
.question-composer {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.question-input {
  width: 100%;
  padding: 8px 12px;
  border: none;
  font-size: 15px;
  font-family: var(--font-serif);
  background: transparent;
  color: var(--text-primary);
  outline: none;
}

.question-input::placeholder {
  color: var(--text-muted);
  font-style: italic;
}

.input-underline {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 1px;
  background: var(--text-accent);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 输入框有内容或聚焦时下划线滑动 */
.input-wrapper.focused .input-underline,
.input-wrapper:focus-within .input-underline {
  width: 100%;
}

/* AI 回复 */
.stream-area {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
}

.stream-answer {
  font-size: 16px;
  line-height: 1.85;
  color: var(--text-primary);
}

.stream-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-accent);
  margin-top: 12px;
  font-size: 14px;
  font-style: italic;
}

.stream-actions {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* 摘录按钮 - 图标 + hover展开文字 */
.excerpt-entry {
  display: flex;
  justify-content: flex-end;
}

.excerpt-expand {
  display: inline-flex;
  align-items: center;
  gap: 0;
  padding: 4px 8px;
  color: var(--text-secondary);
  font-size: 14px;
  font-family: var(--font-serif);
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.excerpt-icon {
  font-size: 16px;
  transition: transform 0.2s ease;
}

.excerpt-text {
  max-width: 0;
  opacity: 0;
  white-space: nowrap;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  margin-left: 0;
}

.excerpt-expand:hover {
  color: var(--text-accent);
  background: color-mix(in srgb, var(--text-accent) 8%, transparent);
}

.excerpt-expand:hover .excerpt-icon {
  transform: scale(1.1);
}

.excerpt-expand:hover .excerpt-text {
  max-width: 100px;
  opacity: 1;
  margin-left: 6px;
}

/* 批注输入 */
.card-input-area {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--border-light);
}

.annotation-input {
  width: 100%;
  padding: 8px 12px;
  border: none;
  font-size: 15px;
  font-family: var(--font-serif);
  background: transparent;
  color: var(--text-primary);
  outline: none;
}

.annotation-input::placeholder {
  color: var(--text-muted);
  font-style: italic;
}

.card-success {
  margin-top: 12px;
  color: var(--success-color);
  font-size: 14px;
  font-style: italic;
}

.card-input-actions {
  display: flex;
  justify-content: flex-end;
  gap: 16px;
  margin-top: 12px;
}
</style>