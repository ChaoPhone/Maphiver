<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import katex from 'katex'
import { extractLatexBlocks } from '@/utils/latex'

marked.setOptions({ breaks: true, gfm: true })

const props = defineProps<{
  content: string
}>()

const emit = defineEmits<{
  (e: 'select', text: string, range: { start: number; end: number; rect: DOMRect | null; firstLineRect: DOMRect | null }): void
}>()

const renderedHtml = computed(() => {
  if (!props.content) return ''
  
  const { text, blocks } = extractLatexBlocks(props.content)
  
  let result = marked.parse(text, { breaks: true, gfm: true }) as string
  
  blocks.forEach(block => {
    try {
      const rendered = katex.renderToString(block.formula, {
        displayMode: block.display,
        throwOnError: false,
        output: 'html',
        trust: true,
      })
      result = result.replace(block.placeholder, rendered)
    } catch (e) {
      console.warn('KaTeX render error for:', block.formula, e)
      result = result.replace(block.placeholder, block.display ? `$$${block.formula}$$` : `$${block.formula}$`)
    }
  })
  
  return result
})

function handleMouseUp(event: MouseEvent) {
  const selection = window.getSelection()
  if (selection && selection.toString().trim()) {
    const text = selection.toString().trim()
    if (text.length >= 1) {
      const range = selection.getRangeAt(0)
      const rect = range.getBoundingClientRect()

      // 获取选区第一行的边界
      let firstLineRect: DOMRect | null = null
      try {
        // 创建一个只包含第一行的临时 range
        const tempRange = document.createRange()
        tempRange.setStart(range.startContainer, range.startOffset)

        // 找到第一行的结束位置（到换行符或 range 结束）
        let endNode = range.endContainer
        let endOffset = range.endOffset

        // 如果结束节点是文本节点，查找第一个换行符
        if (endNode.nodeType === Node.TEXT_NODE) {
          const textContent = endNode.textContent || ''
          const newlineIndex = textContent.indexOf('\n', 0)
          if (newlineIndex !== -1 && newlineIndex < endOffset) {
            endOffset = newlineIndex
          }
        }

        tempRange.setEnd(endNode, endOffset)
        firstLineRect = tempRange.getBoundingClientRect()
        tempRange.detach()
      } catch (e) {
        // 如果计算失败，使用整个选区
        firstLineRect = rect
      }

      emit('select', text, {
        start: range.startOffset,
        end: range.endOffset,
        rect: rect,
        firstLineRect: firstLineRect
      })
    }
  }
}
</script>

<template>
  <div class="formula-renderer" @mouseup="handleMouseUp">
    <div v-html="renderedHtml"></div>
  </div>
</template>

<style scoped>
.formula-renderer {
  font-size: var(--font-size-base);
  line-height: 1.75;
  color: var(--text-primary);
}

.formula-renderer :deep(h1),
.formula-renderer :deep(h2),
.formula-renderer :deep(h3) {
  color: var(--text-primary);
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.formula-renderer :deep(p) {
  margin-bottom: 1em;
}

.formula-renderer :deep(pre) {
  background: var(--bg-hover);
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}

.formula-renderer :deep(code) {
  background: var(--bg-hover);
  padding: 2px 4px;
  border-radius: 2px;
}

.formula-renderer :deep(blockquote) {
  border-left: 4px solid var(--border-color);
  margin: 0;
  padding-left: 16px;
  color: var(--text-secondary);
}

.formula-renderer :deep(.katex) {
  font-size: 1.1em;
}

.formula-renderer :deep(.katex-display) {
  margin: 1em 0;
  overflow-x: auto;
  overflow-y: hidden;
}
</style>