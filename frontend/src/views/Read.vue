<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useSessionStore, useDocumentStore } from '@/stores'
import { marked } from 'marked'
import { ElMessage, ElScrollbar } from 'element-plus'
import { ChatDotRound, Document, ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const sessionStore = useSessionStore()
const documentStore = useDocumentStore()

const loading = ref(true)
const selectedText = ref('')
const question = ref('')
const answering = ref(false)
const streamingAnswer = ref('')
const activeBlockId = ref<string | null>(null)
const showQAPanel = ref(true)

const sessionId = computed(() => route.params.sessionId as string)

const quickQuestions = [
  { type: 'explain', template: '请解释这段内容' },
  { type: 'summary', template: '请总结这段内容的核心要点' },
  { type: 'example', template: '请举例说明这个概念' },
  { type: 'compare', template: '请对比分析这两个概念' },
]

onMounted(async () => {
  try {
    await sessionStore.loadSession(sessionId.value)
    if (sessionStore.currentSession?.document_id) {
      await documentStore.parseDocument(sessionStore.currentSession.document_id)
    }
  } catch (error) {
    ElMessage.error('加载失败')
  }
  loading.value = false
})

function handleTextSelection(blockId: string) {
  const selection = window.getSelection()
  if (selection && selection.toString()) {
    selectedText.value = selection.toString()
    activeBlockId.value = blockId
  }
}

function clearSelection() {
  selectedText.value = ''
  activeBlockId.value = null
  window.getSelection()?.removeAllRanges()
}

async function submitQuestion(qType?: string) {
  if (!question.value.trim() && !qType) {
    ElMessage.warning('请输入问题')
    return
  }
  
  const actualQuestion = qType 
    ? quickQuestions.find(q => q.type === qType)?.template || question.value
    : question.value
  
  answering.value = true
  streamingAnswer.value = ''
  
  try {
    await sessionStore.askQuestion(actualQuestion, selectedText.value, activeBlockId.value || undefined)
    question.value = ''
    selectedText.value = ''
    activeBlockId.value = null
  } catch (error: any) {
    ElMessage.error(error.message || '提问失败')
  }
  
  answering.value = false
}

function goBack() {
  router.push('/')
}

function renderBlockContent(content: string): string {
  return marked.parse(content) as string
}
</script>

<template>
  <div class="read-container">
    <el-container v-loading="loading" element-loading-text="正在加载文档...">
      <el-header class="top-header">
        <el-button :icon="ArrowLeft" @click="goBack">返回首页</el-button>
        <div class="doc-info">
          <el-icon><Document /></el-icon>
          <span>{{ sessionStore.currentSession?.document?.filename || '未知文档' }}</span>
        </div>
        <el-button 
          :icon="ChatDotRound" 
          @click="showQAPanel = !showQAPanel"
          :type="showQAPanel ? 'primary' : 'default'"
        >
          {{ showQAPanel ? '隐藏问答' : '显示问答' }}
        </el-button>
      </el-header>
      
      <el-container>
        <el-main class="content-main">
          <el-scrollbar>
            <div class="blocks-container">
              <div 
                v-for="block in documentStore.blocks" 
                :key="block.id"
                class="content-block"
                :class="{ 'active-block': activeBlockId === block.id }"
                @mouseup="handleTextSelection(block.id)"
              >
                <div class="block-header" v-if="block.chapter_path?.length">
                  <el-tag size="small" type="info">
                    {{ block.chapter_path.join(' > ') }}
                  </el-tag>
                  <el-tag size="small" v-if="block.page">P{{ block.page }}</el-tag>
                </div>
                <div class="block-content" v-html="renderBlockContent(block.content)"></div>
              </div>
              
              <div v-if="documentStore.blocks.length === 0 && !loading" class="empty-content">
                <p>文档内容为空，请重新解析</p>
              </div>
            </div>
          </el-scrollbar>
        </el-main>
        
        <el-aside v-if="showQAPanel" width="400px" class="qa-aside">
          <el-card class="qa-card">
            <template #header>
              <div class="qa-header">
                <span>问答助手</span>
                <el-button size="small" text @click="showQAPanel = false">收起</el-button>
              </div>
            </template>
            
            <el-scrollbar height="300px" class="qa-history">
              <div v-for="msg in sessionStore.qaMessages" :key="msg.id" class="qa-item">
                <div class="qa-question">
                  <el-icon><ChatDotRound /></el-icon>
                  <span>{{ msg.question }}</span>
                </div>
                <div v-if="msg.selected_text" class="qa-context">
                  引用: {{ msg.selected_text.slice(0, 50) }}...
                </div>
                <div class="qa-answer" v-html="marked.parse(msg.answer)"></div>
              </div>
              <div v-if="sessionStore.qaMessages.length === 0" class="qa-empty">
                开始提问，与文档内容互动
              </div>
            </el-scrollbar>
            
            <div class="qa-input-area">
              <div v-if="selectedText" class="selected-preview">
                <el-tag closable @close="clearSelection" type="success">
                  已选中 {{ selectedText.length }} 字
                </el-tag>
                <div class="selected-text-preview">{{ selectedText.slice(0, 100) }}...</div>
              </div>
              
              <div class="quick-buttons">
                <el-button 
                  v-for="q in quickQuestions" 
                  :key="q.type"
                  size="small"
                  round
                  @click="submitQuestion(q.type)"
                  :disabled="answering"
                >
                  {{ q.template.slice(0, 8) }}...
                </el-button>
              </div>
              
              <el-input
                v-model="question"
                placeholder="输入你的问题..."
                :disabled="answering"
                @keyup.enter="submitQuestion()"
              >
                <template #append>
                  <el-button 
                    :icon="ChatDotRound" 
                    @click="submitQuestion()"
                    :loading="answering"
                  />
                </template>
              </el-input>
            </div>
          </el-card>
        </el-aside>
      </el-container>
    </el-container>
  </div>
</template>

<style scoped>
.read-container {
  height: 100vh;
  background: #f5f7fa;
}

.top-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.doc-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
}

.content-main {
  background: #fff;
  padding: 0;
}

.blocks-container {
  padding: 20px;
  max-width: 900px;
}

.content-block {
  margin-bottom: 20px;
  padding: 15px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #e4e7ed;
  transition: all 0.3s;
}

.content-block:hover {
  border-color: #409eff;
}

.active-block {
  border-color: #67c23a;
  background: #f0f9eb;
}

.block-header {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.block-content {
  line-height: 1.8;
  color: #303133;
}

.block-content :deep(h1),
.block-content :deep(h2),
.block-content :deep(h3) {
  margin: 10px 0;
}

.block-content :deep(p) {
  margin: 8px 0;
}

.empty-content {
  text-align: center;
  padding: 50px;
  color: #909399;
}

.qa-aside {
  background: #fff;
  border-left: 1px solid #e4e7ed;
}

.qa-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.qa-history {
  flex: 1;
  margin-bottom: 15px;
}

.qa-item {
  margin-bottom: 15px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.qa-question {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #409eff;
  font-weight: 500;
  margin-bottom: 8px;
}

.qa-context {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  padding: 4px 8px;
  background: #ecf5ff;
  border-radius: 4px;
}

.qa-answer {
  color: #606266;
  line-height: 1.6;
}

.qa-empty {
  text-align: center;
  color: #909399;
  padding: 30px;
}

.qa-input-area {
  border-top: 1px solid #e4e7ed;
  padding-top: 15px;
}

.selected-preview {
  margin-bottom: 10px;
}

.selected-text-preview {
  font-size: 12px;
  color: #67c23a;
  margin-top: 5px;
  padding: 5px;
  background: #f0f9eb;
  border-radius: 4px;
}

.quick-buttons {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}
</style>