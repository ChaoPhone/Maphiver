<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionStore, useDocumentStore } from '@/stores'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'

const route = useRoute()
const sessionStore = useSessionStore()
const documentStore = useDocumentStore()

const loading = ref(true)
const selectedText = ref('')
const question = ref('')
const answering = ref(false)
const currentAnswer = ref('')
const activeBlockId = ref('')

const sessionId = computed(() => route.params.sessionId as string)

const renderedMarkdown = computed(() => {
  return marked(documentStore.rawMarkdown)
})

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

function handleTextSelection() {
  const selection = window.getSelection()
  if (selection && selection.toString()) {
    selectedText.value = selection.toString()
  }
}

async function submitQuestion() {
  if (!question.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  answering.value = true
  currentAnswer.value = ''
  
  try {
    await sessionStore.askQuestion(question.value, selectedText.value, activeBlockId.value)
    question.value = ''
    selectedText.value = ''
  } catch (error: any) {
    ElMessage.error(error.message || '提问失败')
  }
  
  answering.value = false
}

function goBack() {
  window.history.back()
}
</script>

<template>
  <div class="read-container">
    <el-container v-loading="loading">
      <el-aside width="300px">
        <el-card header="问答历史">
          <div v-for="msg in sessionStore.qaMessages" :key="msg.id" class="qa-item">
            <div class="question">{{ msg.question }}</div>
            <div class="answer">{{ msg.answer }}</div>
          </div>
          <div v-if="sessionStore.qaMessages.length === 0" class="empty">
            暂无问答记录
          </div>
        </el-card>
      </el-aside>
      
      <el-main>
        <el-header>
          <el-button @click="goBack">返回</el-button>
          <h3>{{ sessionStore.currentSession?.document?.filename }}</h3>
        </el-header>
        
        <div class="content-area" @mouseup="handleTextSelection">
          <div class="markdown-content" v-html="renderedMarkdown"></div>
        </div>
        
        <el-card class="qa-panel">
          <div v-if="selectedText" class="selected-text">
            <strong>选中内容：</strong>
            <p>{{ selectedText.slice(0, 100) }}{{ selectedText.length > 100 ? '...' : '' }}</p>
          </div>
          
          <el-input
            v-model="question"
            placeholder="输入你的问题..."
            :disabled="answering"
          />
          
          <el-button
            type="primary"
            :loading="answering"
            @click="submitQuestion"
            style="margin-top: 10px"
          >
            提问
          </el-button>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<style scoped>
.read-container {
  height: 100%;
}

.el-aside {
  background: #f5f7fa;
  padding: 10px;
  overflow-y: auto;
}

.el-main {
  display: flex;
  flex-direction: column;
}

.el-header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  border: 1px solid #e4e7ed;
  margin-bottom: 10px;
}

.markdown-content {
  line-height: 1.8;
}

.qa-panel {
  margin-top: auto;
}

.qa-item {
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.question {
  font-weight: bold;
  color: #409eff;
}

.answer {
  margin-top: 5px;
  color: #606266;
}

.selected-text {
  margin-bottom: 10px;
  padding: 10px;
  background: #ecf5ff;
  border-radius: 4px;
}

.empty {
  text-align: center;
  color: #909399;
}
</style>