<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores'

const router = useRouter()
const sessionStore = useSessionStore()

onMounted(async () => {
  await sessionStore.fetchSessions()
})

const goToRead = (sessionId: string) => {
  router.push(`/read/${sessionId}`)
}
</script>

<template>
  <div class="home-view">
    <el-card class="welcome-card">
      <h2>欢迎使用流式知识河</h2>
      <p>上传 PDF 文档，开始智能阅读之旅</p>
      <el-button type="primary" size="large" @click="$router.push('/upload')">
        开始上传
      </el-button>
    </el-card>

    <el-card class="sessions-card" v-if="sessionStore.sessions.length > 0">
      <template #header>
        <span>历史会话</span>
      </template>
      <el-table :data="sessionStore.sessions" style="width: 100%">
        <el-table-column prop="id" label="会话ID" width="300" />
        <el-table-column prop="status" label="状态" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="200" />
        <el-table-column label="操作">
          <template #default="{ row }">
            <el-button size="small" @click="goToRead(row.id)">
              继续阅读
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 800px;
  margin: 0 auto;
}

.welcome-card {
  text-align: center;
  margin-bottom: 20px;
}

.welcome-card h2 {
  margin-bottom: 10px;
}

.welcome-card p {
  color: #666;
  margin-bottom: 20px;
}

.sessions-card {
  margin-top: 20px;
}
</style>