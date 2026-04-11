<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useDocumentStore, useSessionStore } from '@/stores'
import { ElMessage } from 'element-plus'

const router = useRouter()
const documentStore = useDocumentStore()
const sessionStore = useSessionStore()

const loading = ref(false)

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

function goToUpload() {
  router.push('/upload')
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
        <el-button type="primary" @click="goToUpload">上传文档</el-button>
      </el-header>
      
      <el-main v-loading="loading">
        <el-row :gutter="20">
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
</style>