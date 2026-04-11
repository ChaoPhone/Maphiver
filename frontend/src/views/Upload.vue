<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentStore, useSessionStore } from '@/stores'
import { ElMessage, ElProgress } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const router = useRouter()
const documentStore = useDocumentStore()
const sessionStore = useSessionStore()

const fileList = ref<File[]>([])
const uploading = ref(false)
const parsing = ref(false)
const parseProgress = ref(0)
const parseStage = ref('')
const currentDocId = ref('')

function handleFileChange(file: File) {
  fileList.value = [file]
  return false
}

async function handleUpload() {
  if (fileList.value.length === 0) {
    ElMessage.warning('请选择文件')
    return
  }
  
  uploading.value = true
  try {
    const result = await documentStore.uploadFile(fileList.value[0])
    currentDocId.value = result.id
    ElMessage.success('上传成功')
    
    parsing.value = true
    parseStage.value = 'extracting'
    parseProgress.value = 0
    
    await documentStore.parseDocument(result.id)
    
    ElMessage.success('解析完成')
    const session = await sessionStore.createSession(result.id)
    router.push(`/read/${session.id}`)
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
  uploading.value = false
  parsing.value = false
}

function goBack() {
  router.push('/')
}
</script>

<template>
  <div class="upload-container">
    <el-container>
      <el-header>
        <el-button @click="goBack">返回</el-button>
        <h2>上传文档</h2>
      </el-header>
      
      <el-main>
        <el-card>
          <el-upload
            drag
            accept=".pdf"
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :limit="1"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽PDF文件到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">仅支持PDF格式文件</div>
            </template>
          </el-upload>
          
          <el-button
            type="primary"
            :loading="uploading || parsing"
            :disabled="fileList.length === 0"
            @click="handleUpload"
            style="margin-top: 20px"
          >
            {{ parsing ? '解析中...' : uploading ? '上传中...' : '开始上传' }}
          </el-button>
          
          <div v-if="parsing" style="margin-top: 20px">
            <el-progress :percentage="parseProgress" :status="parseProgress === 100 ? 'success' : ''" />
            <p>{{ parseStage }}</p>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<style scoped>
.upload-container {
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.el-header {
  display: flex;
  align-items: center;
  gap: 20px;
}

.el-main {
  max-width: 600px;
}
</style>