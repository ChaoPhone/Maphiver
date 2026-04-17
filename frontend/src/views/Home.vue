<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentStore, useSessionStore } from '@/stores'
import { ElMessage, ElUpload, ElProgress, ElIcon } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const router = useRouter()
const documentStore = useDocumentStore()
const sessionStore = useSessionStore()

const loading = ref(false)
const uploading = ref(false)
const parsing = ref(false)
const parseProgress = ref(0)
const parseStage = ref('')
const fileList = ref<any[]>([])

onMounted(async () => {
  loading.value = true
  try {
    await documentStore.fetchDocuments()
    await sessionStore.fetchSessions()
  } catch (error) {
    ElMessage.error('加载失败')
  }
  loading.value = false
})

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
  parseProgress.value = 0
  parseStage.value = ''
  
  try {
    const result = await documentStore.uploadFile(fileList.value[0].raw)
    ElMessage.success('上传成功')
    
    uploading.value = false
    parsing.value = true
    parseStage.value = '提取文本...'
    parseProgress.value = 10
    
    await documentStore.parseDocument(result.id, (data: any) => {
      if (data.type === 'progress') {
        parseStage.value = data.stage || ''
        parseProgress.value = data.progress || parseProgress.value
      }
    })
    
    parseProgress.value = 100
    parseStage.value = '解析完成'
    ElMessage.success('解析完成')
    
    await documentStore.fetchDocuments()
    const session = await sessionStore.createSession(result.id)
    router.push(`/read/${session.id}`)
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  }
  uploading.value = false
  parsing.value = false
  fileList.value = []
}

async function startReading(documentId: string) {
  try {
    const session = await sessionStore.createSession(documentId)
    router.push(`/read/${session.id}`)
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}

async function continueReading(sessionId: string) {
  router.push(`/read/${sessionId}`)
}
</script>

<template>
  <div class="home-container">
    <el-container>
      <el-header>
        <h1>流式知识河</h1>
      </el-header>
      
      <el-main v-loading="loading">
        <el-row :gutter="20">
          <el-col :span="24">
            <el-card header="上传新文档" class="upload-card">
              <el-upload
                drag
                accept=".pdf,.doc,.docx"
                :auto-upload="false"
                :on-change="handleFileChange"
                :file-list="fileList"
                :limit="1"
                :disabled="uploading || parsing"
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  拖拽文档文件到此处，或<em>点击上传</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">支持 PDF、DOC、DOCX 格式文件</div>
                </template>
              </el-upload>
              
              <el-button
                type="primary"
                :loading="uploading || parsing"
                :disabled="fileList.length === 0"
                @click="handleUpload"
                style="margin-top: 15px"
              >
                {{ parsing ? '解析中...' : uploading ? '上传中...' : '开始解析' }}
              </el-button>
              
              <div v-if="parsing" style="margin-top: 15px">
                <el-progress :percentage="parseProgress" :status="parseProgress === 100 ? 'success' : ''" />
                <p style="margin-top: 8px; color: #606266">{{ parseStage }}</p>
              </div>
            </el-card>
          </el-col>
        </el-row>
        
        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="12">
            <el-card header="文档列表">
              <el-table :data="documentStore.documents" style="width: 100%">
                <el-table-column prop="filename" label="文件名" />
                <el-table-column prop="page_count" label="页数" width="80" />
                <el-table-column prop="created_at" label="上传时间" width="180" />
                <el-table-column label="操作" width="120">
                  <template #default="{ row }">
                    <el-button size="small" type="primary" @click="startReading(row.id)">
                      开始阅读
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
          
          <el-col :span="12">
            <el-card header="阅读会话">
              <el-table :data="sessionStore.sessions" style="width: 100%">
                <el-table-column prop="document?.filename" label="文档" />
                <el-table-column prop="status" label="状态" width="100" />
                <el-table-column prop="updated_at" label="最后更新" width="180" />
                <el-table-column label="操作" width="120">
                  <template #default="{ row }">
                    <el-button size="small" @click="continueReading(row.id)">
                      继续
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<style scoped>
.home-container {
  height: 100%;
}

.el-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f5f7fa;
  padding: 0 20px;
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
}

.upload-card {
  margin-bottom: 20px;
}

.el-icon--upload {
  font-size: 48px;
  color: #409eff;
}
</style>