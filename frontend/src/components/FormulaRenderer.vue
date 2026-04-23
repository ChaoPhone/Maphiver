<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import katex from 'katex'
import { extractLatexBlocks } from '@/utils/latex'

// 配置 marked：启用 GFM 和换行
marked.setOptions({ breaks: true, gfm: true })

const props = defineProps<{
  content: string
}>()

const emit = defineEmits<{
  (e: 'select', text: string, range: { start: number; end: number; rect: DOMRect | null; firstLineRect: DOMRect | null }): void
}>()

const renderedHtml = computed(() => {
  if (!props.content) return ''
  
  // 步骤1: 提取 LaTeX 块并替换为占位符
  // 占位符格式 %%LATEXBLOCK0%% / %%LATEXINLINE0%% 不含 markdown 特殊字符
  const { text, blocks } = extractLatexBlocks(props.content)
  
  // 步骤2: 用 marked 解析 markdown（占位符会被原样保留）
  let result = marked.parse(text, { breaks: true, gfm: true }) as string
  
  // 步骤3: 将占位符替换回 KaTeX 渲染结果
  blocks.forEach(block => {
    try {
      const rendered = katex.renderToString(block.formula, {
        displayMode: block.display,
        throwOnError: false,
        output: 'html',
        trust: true,
      })
      result = replacePlaceholder(result, block.placeholder, rendered)
    } catch (e) {
      console.warn('KaTeX render error for:', block.formula, e)
      const fallback = block.display
        ? `<span class="katex-error">$$${escapeHtml(block.formula)}$$</span>`
        : `<span class="katex-error">$${escapeHtml(block.formula)}$</span>`
      result = replacePlaceholder(result, block.placeholder, fallback)
    }
  })
  
  return result
})

/**
 * 替换占位符：支持多种情况
 * 1. 占位符被完整保留（最常见）
 * 2. 占位符被 <p> 标签包裹（marked 对块级元素使用 <p> 包裹）
 * 3. 占位符被 HTML 标签分割（防御性兜底）
 */
function replacePlaceholder(result: string, placeholder: string, html: string): string {
  // 情况1：直接替换（最常见）
  if (result.indexOf(placeholder) !== -1) {
    result = result.split(placeholder).join(html)
    return result
  }
  
  // 情况2：占位符被 <p> 包裹
  // marked 会把独立的块级内容包裹在 <p> 标签中
  const escapedPlaceholder = escapeRegex(placeholder)
  const wrappedPattern = `<p>${escapedPlaceholder}</p>`
  if (result.indexOf(wrappedPattern) !== -1) {
    result = result.split(wrappedPattern).join(html)
    return result
  }
  
  // 情况3：占位符被 <p> 包裹但含空白符
  const wrappedWithSpace = `<p> ${escapedPlaceholder} </p>`
  if (result.indexOf(wrappedWithSpace) !== -1) {
    result = result.split(wrappedWithSpace).join(html)
    return result
  }
  
  // 情况4：占位符被 HTML 标签分割（防御性兜底）
  // 例如占位符被嵌套在其他标签中
  const chars = placeholder.split('')
  const fuzzyPattern = chars.map(c => {
    if (/[a-zA-Z0-9%]/.test(c)) {
      return `(?:<[^>]*>)*${escapeRegex(c)}`
    }
    return escapeRegex(c)
  }).join('')
  
  // 使用构造函数创建正则，避免 /g 标志带来的 lastIndex 问题
  const fuzzyRegex = new RegExp(fuzzyPattern, 'g')
  const matches = result.match(fuzzyRegex)
  if (matches && matches.length > 0) {
    // 替换所有匹配到的变体
    matches.forEach(match => {
      result = result.replace(match, html)
    })
  }
  
  return result
}

// HTML 转义，用于 KaTeX 渲染失败时的回退显示
function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

// 正则转义
function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

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
  /* 不设置 font-size，继承父元素 markdown-content 的样式 */
  line-height: inherit;
  color: var(--text-primary);
}

/* 只保留公式相关样式，其他样式由 markdown.css 全局控制 */
.formula-renderer :deep(.katex) {
  font-size: 1.1em;
  /* 公式使用数学字体，不受衬线字体影响 */
  font-family: KaTeX_Main, 'Times New Roman', serif;
}

.formula-renderer :deep(.katex-display) {
  margin: 1em 0;
  overflow-x: auto;
  overflow-y: hidden;
}

/* KaTeX 渲染失败的回退样式 */
.formula-renderer :deep(.katex-error) {
  color: var(--error-color, #DC2626);
  font-family: var(--font-mono);
  font-size: 0.9em;
  background: var(--bg-hover);
  padding: 2px 6px;
  border-radius: 4px;
}
</style>
