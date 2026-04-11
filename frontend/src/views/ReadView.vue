<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useSessionStore, useDocumentStore, useQAStore } from '@/stores'
import ReadingPanel from '@/components/ReadingPanel.vue'
import QAPanel from '@/components/QAPanel.vue'

const route = useRoute()
const sessionStore = useSessionStore()
const documentStore = useDocumentStore()
const qaStore = useQAStore()

const sessionId = route.params.sessionId as string
const selectedBlockId = ref<string | null>(null)
const selectedText = ref<string>('')
const showQAPanel = ref(false)

onMounted(async () => {
  await sessionStore.loadSession(sessionId)
  await qaStore.fetchHistory(sessionId)
  await qaStore.fetchQuickQuestions()

  if (sessionStore.currentSession?.document) {
    const doc = sessionStore.currentSession.document
    if (doc.page_count) {
      await documentStore.parseDocument(doc.id)
    }
  }
})

const handleBlockSelect = (blockId: string, text: string) => {
  selectedBlockId.value = blockId
  selectedText.value = text
  showQAPanel.value = true
}

const handleCloseQA = () => {
  showQAPanel.value = false
  selectedBlockId.value = null
  selectedText.value = ''
}
</script>

<template>
  <div class="read-view">
    <el-container>
      <el-main class="reading-area">
        <ReadingPanel
          :blocks="documentStore.blocks"
          :raw-markdown="documentStore.rawMarkdown"
          @block-select="handleBlockSelect"
        />
      </el-main>

      <el-aside v-if="showQAPanel" width="400px" class="qa-area">
        <QAPanel
          :session-id="sessionId"
          :block-id="selectedBlockId"
          :selected-text="selectedText"
          @close="handleCloseQA"
        />
      </el-aside>
    </el-container>
  </div>
</template>

<style scoped>
.read-view {
  height: calc(100vh - 60px);
}

.reading-area {
  padding: 20px;
  overflow-y: auto;
}

.qa-area {
  background-color: #fff;
  border-left: 1px solid #e4e7ed;
  padding: 20px;
}
</style>