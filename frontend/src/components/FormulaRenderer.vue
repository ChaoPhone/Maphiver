<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
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

const rendererRef = ref<HTMLElement | null>(null)

// 实时选区矩形框状态
const selectionBox = ref({
  visible: false,
  top: 0,
  left: 0,
  width: 0,
  height: 0
})

let selectionChangeListener: (() => void) | null = null

const renderedHtml = computed(() => {
  if (!props.content) return ''
  
  // 步骤0: 预处理 - 兼容旧格式占位符
  // 旧格式: %%LATEX_BLOCK_0%% (块级), %%LATEX_INLINE_1%% (行内)
  // 新格式: %%LATEXBLOCK0%% (块级), %%LATEXINLINE1%% (行内)
  // 将旧格式统一转换为新格式，避免 marked 将 _ 解析为斜体
  let content = props.content
  content = content.replace(/%%LATEX_BLOCK_(\d+)%%/g, '%%LATEXBLOCK$1%%')
  content = content.replace(/%%LATEX_INLINE_(\d+)%%/g, '%%LATEXINLINE$1%%')
  
  // 步骤1: 提取 LaTeX 块并替换为占位符
  // 占位符格式 %%LATEXBLOCK0%% / %%LATEXINLINE0%% 不含 markdown 特殊字符
  const { text, blocks } = extractLatexBlocks(content)
  
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

// 更新选区矩形框位置
function updateSelectionBox(rect: DOMRect | null) {
  if (!rect || rect.width === 0 || rect.height === 0) {
    selectionBox.value.visible = false
    return
  }

  const padding = 2
  selectionBox.value = {
    visible: true,
    top: rect.top - padding,
    left: rect.left - padding,
    width: rect.width + padding * 2,
    height: rect.height + padding * 2
  }
}

// 监听选区变化，实时更新矩形框
function handleSelectionChange() {
  const selection = window.getSelection()
  if (!selection || selection.isCollapsed || !selection.toString().trim()) {
    selectionBox.value.visible = false
    return
  }

  try {
    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    updateSelectionBox(rect)
  } catch (e) {
    selectionBox.value.visible = false
  }
}

function handleMouseUp(event: MouseEvent) {
  const selection = window.getSelection()
  if (selection && selection.toString().trim()) {
    const text = selection.toString().trim()
    if (text.length >= 1) {
      const range = selection.getRangeAt(0)
      const rect = range.getBoundingClientRect()

      // 清除浏览器默认选中样式，只显示我们的矩形框
      // 注意：不调用 removeAllRanges()，保持选区状态但不显示蓝色

      // 获取选区第一行的边界
      let firstLineRect: DOMRect | null = null
      try {
        const tempRange = document.createRange()
        tempRange.setStart(range.startContainer, range.startOffset)

        let endNode = range.endContainer
        let endOffset = range.endOffset

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
        firstLineRect = rect
      }

      // 更新矩形框位置
      updateSelectionBox(firstLineRect || rect)

      emit('select', text, {
        start: range.startOffset,
        end: range.endOffset,
        rect: rect,
        firstLineRect: firstLineRect
      })
    }
  }
}

onMounted(() => {
  // 监听选区变化
  selectionChangeListener = () => handleSelectionChange()
  document.addEventListener('selectionchange', selectionChangeListener)
})

onUnmounted(() => {
  if (selectionChangeListener) {
    document.removeEventListener('selectionchange', selectionChangeListener)
  }
})
</script>

<template>
  <div class="formula-renderer" ref="rendererRef" @mouseup="handleMouseUp">
    <div class="markdown-body" v-html="renderedHtml"></div>
    <!-- 实时选区矩形框 -->
    <transition name="selection-fade">
      <div
        v-if="selectionBox.visible"
        class="live-selection-box"
        :style="{
          top: selectionBox.top + 'px',
          left: selectionBox.left + 'px',
          width: selectionBox.width + 'px',
          height: selectionBox.height + 'px'
        }"
      />
    </transition>
  </div>
</template>

<style scoped>
.formula-renderer {
  position: relative;
  line-height: inherit;
  color: var(--text-primary);
}

/* 隐藏浏览器默认的选中样式 */
.formula-renderer ::selection {
  background: transparent;
}

.formula-renderer::-moz-selection {
  background: transparent;
}

/* 实时选区矩形框 - 主题色边框 */
.live-selection-box {
  position: fixed;
  border: 2px solid var(--text-accent);
  border-radius: 2px;
  pointer-events: none;
  z-index: 998;
  background: transparent;
  transition: all 0.1s ease-out;
}

.selection-fade-enter-active,
.selection-fade-leave-active {
  transition: opacity 0.15s ease;
}

.selection-fade-enter-from,
.selection-fade-leave-to {
  opacity: 0;
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
