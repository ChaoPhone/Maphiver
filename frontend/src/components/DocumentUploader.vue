<script setup lang="ts">
import { ref } from 'vue'
import { useDocumentStore } from '@/stores'
import { UploadFilled } from '@element-plus/icons-vue'

const emit = defineEmits<{
  success: [documentId: string]
}>()

const documentStore = useDocumentStore()
const isUploading = ref(false)
const uploadError = ref<string | null>(null)

const handleUpload = async (options: any) => {
  const file = options.file as File

  if (!file.name.endsWith('.pdf')) {
    uploadError.value = '仅支持 PDF 文件'
    return
  }

  isUploading.value = true
  uploadError.value = null

  try {
    const result = await documentStore.uploadDocument(file)
    emit('success', result.id)
  } catch (error: any) {
    uploadError.value = error.message || '上传失败'
    isUploading.value = false
  }
}
</script>

<template>
  <div class="document-uploader">
    <el-upload
      drag
      action="#"
      :auto-upload="true"
      :http-request="handleUpload"
      accept=".pdf"
      :show-file-list="false"
    >
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        将 PDF 文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          仅支持 PDF 格式文件，最大 50MB
        </div>
      </template>
    </el-upload>

    <el-alert
      v-if="uploadError"
      type="error"
      :title="uploadError"
      show-icon
      class="upload-error"
    />

    <el-progress
      v-if="isUploading"
      :percentage="100"
      :indeterminate="true"
      class="upload-progress"
    />
  </div>
</template>

<style scoped>
.document-uploader {
  text-align: center;
}

.upload-error {
  margin-top: 10px;
}

.upload-progress {
  margin-top: 20px;
}
</style>