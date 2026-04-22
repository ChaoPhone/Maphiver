<script setup lang="ts">
import { computed } from 'vue'
import { ElProgress } from 'element-plus'
import FormulaRenderer from './FormulaRenderer.vue'

const props = defineProps<{
  progress: number
  stage: string
  content: string
}>()

const stageLabel = computed(() => {
  const labels: Record<string, string> = {
    'extracting': '提取文本...',
    'extracted': '文本提取完成',
    'formatting': 'AI格式化...',
    'streaming': '流式输出...',
  }
  return labels[props.stage] || props.stage
})
</script>

<template>
  <div class="parsing-view">
    <div class="parse-hero">
      <div class="parse-progress-panel">
        <div class="progress-bar">
          <el-progress :percentage="progress" :stroke-width="6" :show-text="false" />
          <span class="progress-text">{{ progress }}%</span>
        </div>
        <div class="parse-stage">{{ stageLabel }}</div>
      </div>
    </div>
    
    <div class="parsing-layout">
      <div class="parsing-main">
        <div class="parsing-content">
          <div class="stream-output">
            <FormulaRenderer v-if="content" :content="content" />
            <span v-if="stage.includes('格式化')" class="cursor-blink">█</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.parsing-view {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.parse-hero {
  position: sticky;
  top: 0;
  background: var(--bg-main);
  padding: 12px 24px;
  border-bottom: 1px solid var(--border-color);
  z-index: 20;
}

.progress-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar .el-progress {
  flex: 1;
}

.progress-text {
  font-size: var(--font-size-sm);
  color: var(--text-accent);
  font-weight: 500;
  min-width: 40px;
}

.parse-stage {
  margin-top: 8px;
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
}

.parsing-layout {
  flex: 1;
  display: flex;
  padding: 20px;
}

.parsing-main {
  flex: 1;
  min-width: 0;
}

.parsing-content {
  flex: 1;
  padding: 24px 10vw;
  overflow-y: auto;
}

.stream-output {
  font-size: var(--font-size-base);
  line-height: 1.8;
  color: var(--text-primary);
}

.cursor-blink {
  color: var(--text-accent);
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>