<script setup lang="ts">
import { ref } from 'vue'
import { QuestionFilled } from '@element-plus/icons-vue'
import FormulaRenderer from './FormulaRenderer.vue'
import type { QAMessage } from '@/types'

const props = defineProps<{
  messages: QAMessage[]
}>()

const expandedId = ref<string | null>(null)

function toggleExpand(id: string) {
  expandedId.value = expandedId.value === id ? null : id
}
</script>

<template>
  <div class="history-section">
    <div class="history-header">
      <div>
        <div class="history-overline">Conversation Archive</div>
        <span>历史问答</span>
      </div>
      <span class="history-count">{{ messages.length }}</span>
    </div>
    
    <div v-if="messages.length === 0" class="history-empty"></div>
    
    <div v-else class="history-list">
      <div 
        v-for="msg in messages" 
        :key="msg.id" 
        class="history-item"
        :class="{ 'is-expanded': expandedId === msg.id }"
      >
        <div class="history-question" @click="toggleExpand(msg.id)">
          <el-icon><QuestionFilled /></el-icon>
          <span class="question-text">{{ msg.question }}</span>
          <span class="expand-icon">{{ expandedId === msg.id ? '▼' : '▶' }}</span>
        </div>
        <div v-if="expandedId === msg.id" class="history-answer">
          <div class="history-context">"{{ msg.selected_text.slice(0, 90) }}{{ msg.selected_text.length > 90 ? '...' : '' }}"</div>
          <FormulaRenderer :content="msg.answer" />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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

.history-overline {
  font-size: var(--font-size-xs);
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: var(--bg-hover);
  cursor: pointer;
  font-size: var(--font-size-xs);
}

.history-question:hover {
  background: var(--bg-active);
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
  padding: 10px 12px;
  background: var(--bg-card);
  border-top: 1px solid var(--border-light);
  font-size: var(--font-size-xs);
  color: var(--text-primary);
  line-height: 1.6;
}

.history-context {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  background: var(--bg-hover);
  padding: 8px 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  display: block;
  line-height: 1.5;
}
</style>