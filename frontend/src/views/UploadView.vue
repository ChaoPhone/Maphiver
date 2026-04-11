<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentStore, useSessionStore } from '@/stores'
import DocumentUploader from '@/components/DocumentUploader.vue'
import ParseProgress from '@/components/ParseProgress.vue'

const router = useRouter()
const documentStore = useDocumentStore()
const sessionStore = useSessionStore()

const uploadedDocumentId = ref<string | null>(null)
const isUploading = ref(false)

const handleUploadSuccess = async (documentId: string) => {
  uploadedDocumentId.value = documentId
  isUploading.value = false
}

const handleParseComplete = async () => {
  if (uploadedDocumentId.value) {
    const session = await sessionStore.createSession(uploadedDocumentId.value)
    router.push(`/read/${session.id}`)
  }
}
</script>

<template>
  <div class="upload-view">
    <el-card>
      <template #header>
        <span>上传文档</span>
      </template>

      <DocumentUploader
        v-if="!uploadedDocumentId"
        @success="handleUploadSuccess"
      />

      <ParseProgress
        v-if="uploadedDocumentId && documentStore.isParsing"
        :document-id="uploadedDocumentId"
        @complete="handleParseComplete"
      />

      <el-result
        v-if="uploadedDocumentId && !documentStore.isParsing"
        icon="success"
        title="文档解析完成"
        sub-title="点击下方按钮开始阅读"
      >
        <template #extra>
          <el-button type="primary" @click="handleParseComplete">
            开始阅读
          </el-button>
        </template>
      </el-result>
    </el-card>
  </div>
</template>

<style scoped>
.upload-view {
  max-width: 600px;
  margin: 0 auto;
}
</style>