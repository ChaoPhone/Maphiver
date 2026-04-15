<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download, Document, ChatDotRound, Notebook } from '@element-plus/icons-vue'
import type { KnowledgeCard } from '@/types'
import * as api from '@/api'

const props = defineProps<{
  sessionId: string
  documentTitle: string
  rawMarkdown: string
  cards: KnowledgeCard[]
}>()

const exporting = ref(false)
const exportType = ref<'markdown' | 'pdf'>('markdown')

const exportContent = computed(() => {
  let content = `# ${props.documentTitle}\n\n`
  content += `---\n\n`
  content += `## 文档内容\n\n`
  content += props.rawMarkdown || '（无内容）'
  content += `\n\n---\n\n`
  
  if (props.cards.length > 0) {
    content += `## 知识卡片\n\n`
    props.cards.forEach((card, index) => {
      content += `### 卡片 ${index + 1}\n\n`
      content += `**摘录内容：**\n\n${card.source_text}\n\n`
      if (card.annotation) {
        content += `**批注：** ${card.annotation}\n\n`
      }
      content += `---\n\n`
    })
  }
  
  return content
})

async function exportMarkdown() {
  exporting.value = true
  try {
    const blob = new Blob([exportContent.value], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${props.documentTitle.replace(/\.[^/.]+$/, '')}_export.md`
    link.click()
    URL.revokeObjectURL(url)
    ElMessage.success('Markdown 导出成功')
  } catch (error: any) {
    ElMessage.error('导出失败: ' + error.message)
  }
  exporting.value = false
}

async function exportPDF() {
  exporting.value = true
  try {
    const contentEl = document.querySelector('.markdown-content')
    if (!contentEl) {
      ElMessage.warning('无法找到文档内容')
      return
    }
    
    const printWindow = window.open('', '_blank')
    if (!printWindow) {
      ElMessage.warning('无法打开打印窗口')
      return
    }
    
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>${props.documentTitle}</title>
        <style>
          body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
          h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }
          h2 { margin-top: 30px; border-bottom: 1px solid #ccc; }
          h3 { margin-top: 20px; }
          pre { background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }
          code { background: #f5f5f5; padding: 2px 4px; border-radius: 2px; }
          blockquote { border-left: 4px solid #ddd; margin: 0; padding-left: 16px; color: #666; }
          .katex { font-size: 1.1em; }
          .card-section { margin-top: 40px; padding: 20px; background: #f9f9f9; border-radius: 8px; }
          .card-source { margin: 10px 0; padding: 10px; background: #fff; border: 1px solid #eee; }
          .card-annotation { color: #666; margin-top: 8px; }
        </style>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
      </head>
      <body>
        ${generatePrintContent()}
        <script>
          window.onload = function() { window.print(); }
        </script>
      </body>
      </html>
    `)
    printWindow.document.close()
    ElMessage.success('PDF 打印窗口已打开')
  } catch (error: any) {
    ElMessage.error('导出失败: ' + error.message)
  }
  exporting.value = false
}

function generatePrintContent(): string {
  let html = `<h1>${props.documentTitle}</h1>`
  html += `<hr>`
  html += `<h2>文档内容</h2>`
  html += `<div class="content">${props.rawMarkdown || '<p>（无内容）</p>'}</div>`
  
  if (props.cards.length > 0) {
    html += `<hr>`
    html += `<h2>知识卡片</h2>`
    props.cards.forEach((card, index) => {
      html += `<div class="card-section">`
      html += `<h3>卡片 ${index + 1}</h3>`
      html += `<div class="card-source"><strong>摘录内容：</strong><br>${card.source_text}</div>`
      if (card.annotation) {
        html += `<div class="card-annotation"><strong>批注：</strong> ${card.annotation}</div>`
      }
      html += `</div>`
    })
  }
  
  return html
}

async function handleExport() {
  if (exportType.value === 'markdown') {
    await exportMarkdown()
  } else {
    await exportPDF()
  }
}
</script>

<template>
  <el-card class="export-panel">
    <template #header>
      <div class="panel-header">
        <el-icon><Download /></el-icon>
        <span>导出文档</span>
      </div>
    </template>

    <div class="export-options">
      <el-radio-group v-model="exportType" size="small">
        <el-radio-button value="markdown">
          <el-icon><Document /></el-icon>
          Markdown
        </el-radio-button>
        <el-radio-button value="pdf">
          <el-icon><Document /></el-icon>
          PDF
        </el-radio-button>
      </el-radio-group>
    </div>

    <div class="export-preview">
      <div class="preview-label">导出内容包含：</div>
      <div class="preview-items">
        <el-tag size="small" type="info">
          <el-icon><Document /></el-icon>
          文档内容
        </el-tag>
        <el-tag size="small" type="warning" v-if="cards.length > 0">
          <el-icon><Notebook /></el-icon>
          {{ cards.length }} 张知识卡片
        </el-tag>
      </div>
    </div>

    <el-button 
      type="primary" 
      :icon="Download"
      :loading="exporting"
      @click="handleExport"
      style="width: 100%"
    >
      {{ exportType === 'markdown' ? '下载 Markdown' : '打印 PDF' }}
    </el-button>
  </el-card>
</template>

<style scoped>
.export-panel {
  margin-bottom: 15px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.export-options {
  margin-bottom: 15px;
}

.export-preview {
  margin-bottom: 15px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.preview-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
}

.preview-items {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>