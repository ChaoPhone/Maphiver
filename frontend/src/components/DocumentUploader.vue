<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElUpload, ElIcon } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import * as api from '@/api'

const emit = defineEmits<{
  (e: 'uploaded', documentId: string, sessionId: string): void
}>()

const uploading = ref(false)
const fileList = ref<any[]>([])

function handleFileChange(uploadFile: any) {
  fileList.value = [uploadFile]
  return false
}

async function handleUpload() {
  if (fileList.value.length === 0 || !fileList.value[0].raw) {
    ElMessage.warning('请选择文件')
    return
  }

  uploading.value = true

  try {
    const result = await api.uploadDocument(fileList.value[0].raw)

    const session = await api.createSession(result.id)

    fileList.value = []
    ElMessage.success('上传成功，正在跳转...')
    emit('uploaded', result.id, session.id)
  } catch (error: any) {
    ElMessage.error(error.message || '上传失败')
  }

  uploading.value = false
}
</script>

<template>
  <div class="upload-area">
    <el-upload
      drag
      accept=".pdf,.doc,.docx"
      :auto-upload="false"
      :on-change="handleFileChange"
      :file-list="fileList"
      :limit="1"
      :disabled="uploading"
      class="compact-uploader"
    >
      <el-icon class="upload-icon"><upload-filled /></el-icon>
      <div class="upload-text">拖拽文档到此处，或<em>点击选择</em></div>
    </el-upload>

    <transition name="fade-slide">
      <el-button
        v-if="fileList.length > 0"
        type="primary"
        :loading="uploading"
        @click="handleUpload"
        class="upload-btn"
      >
        {{ uploading ? '上传中...' : '开始解析' }}
      </el-button>
    </transition>
  </div>
</template>

<style scoped>
.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 20px 0;
}

.compact-uploader {
  width: 100%;
  max-width: 400px;
}

.compact-uploader :deep(.el-upload-dragger) {
  padding: 24px 20px;
}

.upload-icon {
  font-size: 32px;
  color: var(--text-accent);
}

.upload-text {
  margin-top: 8px;
  color: var(--text-secondary);
  font-size: var(--font-size-sm);
}

.upload-text em {
  color: var(--text-accent);
}

.upload-btn {
  width: 100%;
  max-width: 400px;
  height: 40px;
  background: var(--text-accent);
  border-color: var(--text-accent);
  color: white;
  font-weight: 500;
}

.upload-btn:hover {
  opacity: 0.9;
  background: var(--text-accent);
  border-color: var(--text-accent);
}

/* 按钮显示动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>