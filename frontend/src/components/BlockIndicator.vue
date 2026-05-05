<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from 'vue'
import FormulaRenderer from './FormulaRenderer.vue'
import { findRelatedQA } from '@/utils/qaMatch'
import type { QAMessage } from '@/types'

const props = defineProps<{
  container: HTMLElement
  qaMessages: QAMessage[]
  refreshTrigger?: number
}>()

const emit = defineEmits<{
  (e: 'block-select', text: string, rect: DOMRect): void
  (e: 'panel-expanded', isExpanded: boolean): void
}>()

// Block信息
interface BlockInfo {
  element: HTMLElement
  top: number
  height: number
  indicatorTop: number
  indicatorHeight: number
  text: string
}

const blocks = ref<BlockInfo[]>([])
const scrollTop = ref(0)

// 鼠标Y坐标（用于找最近的block）
const mouseY = ref(0)
// 是否启用鼠标追踪（鼠标在右侧QA区域时启用）
const mouseTrackingEnabled = ref(false)

// 当前鼠标最近的block索引
const autoExpandedBlockIndex = ref<number | null>(null)
// QA卡片展开状态：点击触发
const expandedBlockIndex = ref<number | null>(null)
const expandedQAId = ref<string | null>(null)

// 追问状态
const followUpQuestion = ref('')
const followUpAnswering = ref(false)
const followUpMessages = ref<Map<string, QAMessage[]>>(new Map())

const BLOCK_SELECTOR = 'h1, h2, h3, h4, h5, h6, p, ul, ol, pre, blockquote, table'
const BLOCK_PARENT_TAGS = ['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'P', 'UL', 'OL', 'PRE', 'BLOCKQUOTE', 'TABLE', 'LI']

// QA节点间距
const NODE_HEIGHT = 28
const BRACKET_PADDING = 24
// QA节点最大可见数量（超过时内部滚动）
const MAX_VISIBLE_NODES = 10

function isNestedBlock(el: HTMLElement): boolean {
  let parent = el.parentElement
  while (parent && parent !== props.container) {
    if (BLOCK_PARENT_TAGS.includes(parent.tagName)) return true
    parent = parent.parentElement
  }
  return false
}

function calculateBlocks() {
  if (!props.container) return

  const containerRect = props.container.getBoundingClientRect()
  const elements = props.container.querySelectorAll(BLOCK_SELECTOR)
  const newBlocks: BlockInfo[] = []

  const scrollContainer = props.container.closest('.scroll-container') as HTMLElement
  const currentScrollTop = scrollContainer?.scrollTop || 0

  elements.forEach((el) => {
    const element = el as HTMLElement
    if (isNestedBlock(element)) return

    const rect = element.getBoundingClientRect()
    if (rect.height < 20) return

    const relativeTop = rect.top - containerRect.top + currentScrollTop
    const indicatorHeight = Math.max(8, rect.height / 3)
    const indicatorTop = relativeTop + (rect.height - indicatorHeight) / 2

    const text = element.textContent?.trim() || ''
    if (!text) return

    newBlocks.push({
      element,
      top: relativeTop,
      height: rect.height,
      indicatorTop,
      indicatorHeight,
      text
    })
  })

  blocks.value = newBlocks
  updateAutoExpandedBlock()
}

const blocksWithQA = computed(() => {
  return blocks.value.filter(block =>
    findRelatedQA(block.text, props.qaMessages).length > 0
  )
})

// 获取block的当前视口位置
function getBlockViewportTop(block: BlockInfo): number {
  const scrollContainer = props.container?.closest('.scroll-container') as HTMLElement
  const scrollRect = scrollContainer?.getBoundingClientRect() || { top: 0 }
  return block.indicatorTop - scrollTop.value + scrollRect.top
}

// 根据鼠标Y坐标找最近的block
function updateAutoExpandedBlock() {
  if (blocksWithQA.value.length === 0) return
  if (expandedBlockIndex.value !== null) return // 卡片展开时不更新

  // 如果鼠标追踪未启用，不显示任何卡片
  if (!mouseTrackingEnabled.value) {
    autoExpandedBlockIndex.value = null
    return
  }

  const targetY = mouseY.value

  let closestBlock: { index: number; distance: number } | null = null

  blocksWithQA.value.forEach((block, idx) => {
    const blockViewportTop = getBlockViewportTop(block)
    const blockCenter = blockViewportTop + block.indicatorHeight / 2
    const distance = Math.abs(blockCenter - targetY)

    // 只考虑鼠标附近的block（距离不超过300px）
    if (distance < 300 && (!closestBlock || distance < closestBlock.distance)) {
      closestBlock = { index: idx, distance }
    }
  })

  autoExpandedBlockIndex.value = closestBlock?.index ?? null
}

// 计算QA节点数量（全部展示）
function getQANodeCount(blockIndex: number): number {
  const block = blocksWithQA.value[blockIndex]
  if (!block) return 0
  return findRelatedQA(block.text, props.qaMessages).length
}

// 动态计算大括号高度（基于所有QA节点）
function getBracketHeight(blockIndex: number): number {
  const nodeCount = Math.min(getQANodeCount(blockIndex), MAX_VISIBLE_NODES)
  return nodeCount * NODE_HEIGHT + BRACKET_PADDING
}

// 动态生成大括号SVG path
function getBracketPath(height: number): string {
  const halfHeight = height / 2
  const curveWidth = 12
  const curveDepth = 8

  return `M 26 0
          C 20 0, ${14 - curveDepth} ${curveWidth}, 14 ${curveWidth * 1.5}
          L 14 ${halfHeight - curveWidth}
          C 14 ${halfHeight - curveWidth/2}, 8 ${halfHeight}, 0 ${halfHeight}
          C 8 ${halfHeight}, 14 ${halfHeight + curveWidth/2}, 14 ${halfHeight + curveWidth}
          L 14 ${height - curveWidth * 1.5}
          C ${14 - curveDepth} ${height - curveWidth}, 20 ${height}, 26 ${height}`
}

// QA节点点击展开详情卡片
function handleQANodeClick(blockIndex: number, qa: QAMessage, event: MouseEvent) {
  event.stopPropagation()
  event.preventDefault()

  if (expandedBlockIndex.value === blockIndex && expandedQAId.value === qa.id) {
    closeCard()
  } else {
    expandedBlockIndex.value = blockIndex
    expandedQAId.value = qa.id
    autoExpandedBlockIndex.value = null
    emit('panel-expanded', true)
  }
}

function closeCard() {
  expandedBlockIndex.value = null
  expandedQAId.value = null
  emit('panel-expanded', false)
  updateAutoExpandedBlock()
}

function handleDocumentClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  if (target.closest('.qa-tree') || target.closest('.qa-card-overlay')) return
  closeCard()
}

// 追问功能
async function submitFollowUp(qa: QAMessage) {
  if (!followUpQuestion.value.trim()) return

  followUpAnswering.value = true

  const newFollowUp: QAMessage = {
    id: 'followup-' + Date.now(),
    session_id: qa.session_id,
    question: followUpQuestion.value,
    selected_text: qa.selected_text,
    answer: '',
    created_at: new Date().toISOString()
  }

  if (!followUpMessages.value.has(qa.id)) {
    followUpMessages.value.set(qa.id, [])
  }
  followUpMessages.value.get(qa.id)!.push(newFollowUp)

  // 模拟回答（实际应该调用 API）
  setTimeout(() => {
    newFollowUp.answer = '这是追问的回答内容...'
    followUpAnswering.value = false
    followUpQuestion.value = ''
  }, 1000)
}

function getFollowUps(qaId: string): QAMessage[] {
  return followUpMessages.value.get(qaId) || []
}

// Observers
let resizeObserver: ResizeObserver | null = null
let mutationObserver: MutationObserver | null = null
let scrollHandler: (() => void) | null = null
let actualScrollContainer: HTMLElement | null = null
let mouseMoveHandler: ((e: MouseEvent) => void) | null = null

function setupObservers() {
  if (!props.container) return
  resizeObserver = new ResizeObserver(() => nextTick(calculateBlocks))
  resizeObserver.observe(props.container)
  mutationObserver = new MutationObserver(() => nextTick(calculateBlocks))
  mutationObserver.observe(props.container, { childList: true, subtree: true })

  // 滚动监听：更新scrollTop和QA卡片位置
  actualScrollContainer = props.container.closest('.scroll-container') as HTMLElement
  if (actualScrollContainer) {
    scrollHandler = () => {
      scrollTop.value = actualScrollContainer?.scrollTop || 0
      nextTick(updateAutoExpandedBlock)
    }
    actualScrollContainer.addEventListener('scroll', scrollHandler, { passive: true })
  }

  // 鼠标移动监听：追踪鼠标Y坐标，判断是否在右侧区域
  mouseMoveHandler = (e: MouseEvent) => {
    const thresholdX = window.innerWidth * 0.75 - 20  // 75vw位置向左20px

    // 判断鼠标是否在右侧QA区域
    if (e.clientX >= thresholdX) {
      mouseTrackingEnabled.value = true
      mouseY.value = e.clientY
    } else {
      mouseTrackingEnabled.value = false
      autoExpandedBlockIndex.value = null
    }

    nextTick(updateAutoExpandedBlock)
  }
  document.addEventListener('mousemove', mouseMoveHandler, { passive: true })
}

function cleanupObservers() {
  if (resizeObserver) resizeObserver.disconnect()
  if (mutationObserver) mutationObserver.disconnect()
  if (scrollHandler && actualScrollContainer) {
    actualScrollContainer.removeEventListener('scroll', scrollHandler)
    actualScrollContainer = null
  }
  if (mouseMoveHandler) {
    document.removeEventListener('mousemove', mouseMoveHandler)
    mouseMoveHandler = null
  }
}

watch(() => props.container, (newContainer, oldContainer) => {
  if (oldContainer) cleanupObservers()
  if (newContainer) nextTick(() => {
    calculateBlocks()
    setupObservers()
  })
}, { immediate: true })

// 监听qaMessages变化，重新计算blocks
watch(() => props.qaMessages, () => {
  nextTick(calculateBlocks)
}, { deep: true })

// 监听外部刷新触发器
watch(() => props.refreshTrigger, () => {
  nextTick(calculateBlocks)
})

onMounted(() => document.addEventListener('click', handleDocumentClick))
onUnmounted(() => {
  cleanupObservers()
  document.removeEventListener('click', handleDocumentClick)
})
</script>

<template>
  <div class="block-indicator-wrapper">
    <!-- QA 树：根据鼠标竖直位置触发，只显示一张卡片 -->
    <div
      v-for="(block, blockIndex) in blocksWithQA"
      :key="'tree-' + blockIndex"
      class="qa-tree"
      :class="{
        'is-visible': autoExpandedBlockIndex === blockIndex || expandedBlockIndex === blockIndex
      }"
      :style="{ top: getBlockViewportTop(block) + block.indicatorHeight / 2 + 'px' }"
      @click.stop
    >
      <!-- 大括号 SVG -->
      <svg
        class="bracket"
        :viewBox="`0 0 28 ${getBracketHeight(blockIndex)}`"
        :style="{
          height: getBracketHeight(blockIndex) + 'px',
          top: -getBracketHeight(blockIndex) / 2 + 'px'
        }"
      >
        <path
          :d="getBracketPath(getBracketHeight(blockIndex))"
          stroke-width="2"
          stroke-linecap="round"
          fill="none"
        />
      </svg>

      <!-- QA 节点列表（全部展示，最多10条可见） -->
      <div class="qa-nodes" :class="{ 'has-scroll': getQANodeCount(blockIndex) > MAX_VISIBLE_NODES }">
        <template v-for="(qa, qaIndex) in findRelatedQA(block.text, props.qaMessages)" :key="qa.id">
          <div
            class="qa-node"
            :style="{ transform: `translateY(${(qaIndex - Math.min(getQANodeCount(blockIndex), MAX_VISIBLE_NODES) / 2) * NODE_HEIGHT}px)` }"
            @click="handleQANodeClick(blockIndex, qa, $event)"
          >
            <span class="dot"></span>
            <span class="node-text">{{ qa.question.slice(0, 12) }}{{ qa.question.length > 12 ? '...' : '' }}</span>
            <span class="underline"></span>
          </div>
        </template>

        <!-- 更多提示（超过10条时显示） -->
        <div
          v-if="getQANodeCount(blockIndex) > MAX_VISIBLE_NODES"
          class="scroll-hint"
          :style="{ transform: `translateY(${(MAX_VISIBLE_NODES - Math.min(getQANodeCount(blockIndex), MAX_VISIBLE_NODES) / 2) * NODE_HEIGHT + 20}px)` }"
        >
          滚动查看更多...
        </div>
      </div>
    </div>
  </div>

  <!-- 遮罩层：点击关闭 -->
  <transition name="overlay-fade">
    <div
      v-if="expandedBlockIndex !== null && expandedQAId"
      class="qa-card-overlay"
      @click="closeCard"
    />
  </transition>

  <!-- QA 详情卡片：固定在右侧，借鉴QAPanel风格 -->
  <transition name="qa-card-fade">
    <div
      v-if="expandedBlockIndex !== null && expandedQAId"
      class="qa-detail-card"
    >
      <!-- 折页关闭按钮 -->
      <div class="fold-corner" @click="closeCard">
        <div class="fold-paper"></div>
        <div class="fold-x">
          <svg width="12" height="12" viewBox="0 0 12 12">
            <line x1="2" y1="2" x2="10" y2="10" stroke="currentColor" stroke-width="1.5"/>
            <line x1="10" y1="2" x2="2" y2="10" stroke="currentColor" stroke-width="1.5"/>
          </svg>
        </div>
      </div>

      <template v-for="(block, blockIndex) in blocksWithQA" :key="blockIndex">
        <template v-if="expandedBlockIndex === blockIndex">
          <template v-for="qa in findRelatedQA(block.text, props.qaMessages)" :key="qa.id">
            <div v-if="expandedQAId === qa.id">
              <!-- 选区引用 -->
              <blockquote class="context-quote">
                {{ qa.selected_text.slice(0, 200) }}{{ qa.selected_text.length > 200 ? '...' : '' }}
              </blockquote>

              <!-- AI回答 -->
              <div class="answer-content">
                <FormulaRenderer :content="qa.answer" />
              </div>

              <!-- 追问记录 -->
              <div v-if="getFollowUps(qa.id).length > 0" class="follow-up-section">
                <div class="section-divider">追问记录</div>
                <div v-for="fqa in getFollowUps(qa.id)" :key="fqa.id" class="follow-up-item">
                  <div class="fq-label">Q: {{ fqa.question }}</div>
                  <div class="fq-answer">
                    <FormulaRenderer :content="fqa.answer" />
                  </div>
                </div>
              </div>

              <!-- 追问输入 - 借鉴QAPanel下划线滑动风格 -->
              <div class="follow-up-composer">
                <div class="input-wrapper" :class="{ focused: followUpQuestion.length > 0 }">
                  <input
                    v-model="followUpQuestion"
                    type="text"
                    placeholder="输入追问..."
                    class="follow-up-input"
                    :disabled="followUpAnswering"
                    @keyup.enter="submitFollowUp(qa)"
                  />
                  <span class="input-underline"></span>
                </div>
                <span
                  class="action-link primary"
                  :class="{ disabled: followUpAnswering || !followUpQuestion.trim() }"
                  @click="!followUpAnswering && followUpQuestion.trim() && submitFollowUp(qa)"
                >
                  <span class="link-text">{{ followUpAnswering ? '思考中' : '追问' }}</span>
                  <span class="link-underline"></span>
                </span>
              </div>
            </div>
          </template>
        </template>
      </template>
    </div>
  </transition>
</template>

<style scoped>
/* Wrapper：透明区域，不阻止其他交互 */
.block-indicator-wrapper {
  position: fixed;
  left: 75vw;
  top: 0;
  width: 25vw;
  height: 100vh;
  pointer-events: none;  /* 透明，不阻止滚动等交互 */
  background: transparent;
  z-index: 50;
}

/* QA 树：根据鼠标竖直位置触发，只显示一张卡片 */
.qa-tree {
  position: absolute;
  left: 0;
  pointer-events: auto;
  z-index: 10;
  opacity: 0;
  transition: opacity 300ms ease-out;
}

.qa-tree.is-visible {
  opacity: 1;
}

/* 大括号 */
.bracket {
  position: absolute;
  left: 0;
  width: 28px;
  opacity: 0.3;
}

.bracket path {
  stroke: var(--text-accent);
}

/* QA节点容器（支持内部滚动） */
.qa-nodes {
  position: relative;
}

.qa-nodes.has-scroll {
  max-height: 280px;
  overflow-y: auto;
  scrollbar-width: thin;
}

.qa-nodes.has-scroll::-webkit-scrollbar {
  width: 4px;
}

.qa-nodes.has-scroll::-webkit-scrollbar-track {
  background: transparent;
}

.qa-nodes.has-scroll::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 2px;
}

/* QA节点 */
.qa-node {
  position: absolute;
  left: 28px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 0;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s ease;
}

.qa-node:hover {
  background: color-mix(in srgb, var(--bg-hover) 50%, transparent);
  border-radius: 4px;
}

.dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--text-accent);
  opacity: 0.5;
}

.qa-node:hover .dot {
  opacity: 1;
}

.node-text {
  font-size: 15px;
  color: var(--text-secondary);
}

.qa-node:hover .node-text {
  color: var(--text-accent);
}

.underline {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--text-accent);
  opacity: 0;
  transform: scaleX(0);
  transition: all 0.2s ease;
}

.qa-node:hover .underline {
  opacity: 0.4;
  transform: scaleX(1);
}

/* 滚动提示 */
.scroll-hint {
  position: absolute;
  left: 32px;
  font-size: 14px;
  color: var(--text-muted);
  opacity: 0.7;
}

/* 遮罩层 */
.qa-card-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.2);
}

.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.2s ease;
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}

/* QA 详情卡片：固定在右侧，左边缘接近75vw主文档边界 */
.qa-detail-card {
  position: fixed;
  left: calc(75vw + 10px);  /* 左侧接近主文档右边缘，留10px间距 */
  right: 20px;  /* 右边距20px */
  top: 60px;
  max-height: calc(100vh - 100px);
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 24px;
  padding-top: 32px;
  z-index: 1000;
  overflow-y: auto;
  font-family: var(--font-serif);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  animation: card-slide-in 0.3s ease-out;
}

@keyframes card-slide-in {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.qa-card-fade-enter-active,
.qa-card-fade-leave-active {
  transition: all 0.3s ease-out;
}

.qa-card-fade-enter-from,
.qa-card-fade-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.qa-detail-card::-webkit-scrollbar {
  width: 5px;
}

.qa-detail-card::-webkit-scrollbar-track {
  background: transparent;
}

.qa-detail-card::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

/* 折页关闭按钮 */
.fold-corner {
  position: absolute;
  top: 0;
  right: 0;
  width: 36px;
  height: 36px;
  cursor: pointer;
  overflow: visible;
}

.fold-paper {
  position: absolute;
  top: 0;
  right: 0;
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, var(--bg-card) 50%, var(--bg-hover) 50%);
  clip-path: polygon(0 0, 100% 0, 100% 100%);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: top right;
}

.fold-x {
  position: absolute;
  top: 10px;
  right: 10px;
  color: transparent;
  opacity: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fold-corner:hover .fold-paper {
  background: linear-gradient(135deg, var(--bg-card) 50%, var(--text-accent) 50%);
  transform: rotate(-15deg) scale(1.1);
  clip-path: polygon(0 0, 100% 0, 100% 80%, 80% 100%);
}

.fold-corner:hover .fold-x {
  color: var(--text-accent);
  opacity: 1;
  transform: translate(2px, 2px);
}

/* 选区引用 */
.context-quote {
  margin: 0 0 20px 0;
  padding: 12px 16px;
  border-left: 4px solid var(--text-accent);
  background: var(--bg-note);
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.8;
  font-style: italic;
}

/* AI回答 */
.answer-content {
  font-size: 16px;
  line-height: 1.85;
  color: var(--text-primary);
}

/* 追问记录 */
.follow-up-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
}

.section-divider {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 12px;
}

.follow-up-item {
  padding: 12px;
  background: var(--bg-hover);
  border-radius: 8px;
  margin-bottom: 10px;
}

.fq-label {
  font-size: 15px;
  color: var(--text-accent);
  margin-bottom: 8px;
}

.fq-answer {
  font-size: 15px;
  color: var(--text-primary);
  line-height: 1.6;
}

/* 追问输入 - 下划线滑动风格 */
.follow-up-composer {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border-light);
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-wrapper {
  flex: 1;
  position: relative;
}

.follow-up-input {
  width: 100%;
  padding: 8px 12px;
  border: none;
  font-size: 15px;
  font-family: var(--font-serif);
  background: transparent;
  color: var(--text-primary);
  outline: none;
}

.follow-up-input::placeholder {
  color: var(--text-muted);
  font-style: italic;
}

.input-underline {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 1px;
  background: var(--text-accent);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.input-wrapper.focused .input-underline,
.input-wrapper:focus-within .input-underline {
  width: 100%;
}

/* 下划线滑动按钮 */
.action-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 0;
  color: var(--text-secondary);
  font-size: 14px;
  font-family: var(--font-serif);
  cursor: pointer;
  position: relative;
  transition: color 0.2s ease;
}

.action-link.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.link-text {
  position: relative;
  z-index: 1;
}

.link-underline {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 0;
  height: 1px;
  background: var(--text-accent);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.action-link:hover:not(.disabled) {
  color: var(--text-accent);
}

.action-link:hover:not(.disabled) .link-underline {
  width: 100%;
}

.action-link.primary {
  color: var(--text-accent);
  font-weight: 500;
}
</style>