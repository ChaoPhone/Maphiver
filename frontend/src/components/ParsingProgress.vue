<script setup lang="ts">
import { computed } from 'vue'
import { ElProgress, ElButton } from 'element-plus'
import { VideoPause, VideoPlay, Close } from '@element-plus/icons-vue'
import FormulaRenderer from './FormulaRenderer.vue'

const props = defineProps<{
  progress: number
  stage: string
  content: string
  isPaused?: boolean
}>()

const emit = defineEmits<{
  pause: []
  resume: []
  stop: []
}>()

const stageLabel = computed(() => {
  const labels: Record<string, string> = {
    'extracting': '提取文本...',
    'extracted': '文本提取完成',
    'formatting': 'AI格式化...',
    'streaming': '流式输出...',
    'stopped': '已停止',
    'done': '完成',
  }
  return labels[props.stage] || props.stage
})

const isFormatting = computed(() => {
  return props.stage === 'formatting' || props.stage === 'streaming'
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
      <!-- 右侧控制栏 -->
      <div class="parsing-sidebar">
        <div class="control-panel">
          <div class="control-title">格式化控制</div>
          <div class="control-buttons">
            <el-button
              v-if="isFormatting && !isPaused"
              type="warning"
              size="small"
              :icon="VideoPause"
              @click="emit('pause')"
              circle
              title="暂停显示"
            />
            <el-button
              v-if="isFormatting && isPaused"
              type="success"
              size="small"
              :icon="VideoPlay"
              @click="emit('resume')"
              circle
              title="继续显示"
            />
            <el-button
              v-if="isFormatting"
              type="danger"
              size="small"
              :icon="Close"
              @click="emit('stop')"
              circle
              title="停止格式化"
            />
          </div>
          <div v-if="isPaused" class="paused-hint">
            已暂停接收，后台继续处理
          </div>
        </div>
      </div>
      
      <div class="parsing-main">
        <div class="parsing-content">
          <div class="stream-output">
            <FormulaRenderer v-if="content" :content="content" />
            <span v-if="stage.includes('格式化') && !isPaused" class="cursor-blink">█</span>
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
  gap: 20px;
}

.parsing-sidebar {
  width: 200px;
  flex-shrink: 0;
}

.control-panel {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  position: sticky;
  top: 80px;
}

.control-title {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.control-buttons {
  display: flex;
  gap: 8px;
  justify-content: center;
  margin-bottom: 12px;
}

.paused-hint {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  text-align: center;
  padding: 8px;
  background: rgba(255, 193, 7, 0.1);
  border-radius: 4px;
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