<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { ElIcon, ElButton, ElScrollbar } from 'element-plus'
import { Notebook, EditPen, Close } from '@element-plus/icons-vue'
import FootprintPanel from './FootprintPanel.vue'
import FormulaRenderer from './FormulaRenderer.vue'
import type { KnowledgeCard } from '@/types'
import * as api from '@/api'

const props = defineProps<{
  sessionId: string
  cardsRefreshTrigger?: number
}>()

const cards = ref<KnowledgeCard[]>([])
const cardsLoading = ref(false)

const cardCount = computed(() => cards.value.length)

async function loadCards() {
  if (!props.sessionId) return
  cardsLoading.value = true
  try {
    cards.value = await api.getCards(props.sessionId)
  } catch (error) {
    console.error('加载卡片失败', error)
  }
  cardsLoading.value = false
}

async function deleteCard(cardId: string) {
  try {
    await api.deleteCard(cardId)
    await loadCards()
  } catch (error: any) {
    console.error('删除失败', error)
  }
}

// 监听刷新触发器
watch(() => props.cardsRefreshTrigger, () => {
  loadCards()
})

onMounted(() => {
  loadCards()
})
</script>

<template>
  <aside class="sidebar-hover">
    <div class="sidebar-content">
      <div class="cards-section">
        <div class="section-header">
          <el-icon><Notebook /></el-icon>
          <span>知识卡片</span>
          <span class="section-count">{{ cardCount }}</span>
        </div>
        
        <el-scrollbar height="180px">
          <div v-if="cards.length > 0" class="cards-list">
            <div v-for="card in cards" :key="card.id" class="card-item">
              <div class="card-source">{{ card.source_text.slice(0, 60) }}{{ card.source_text.length > 60 ? '...' : '' }}</div>
              <div v-if="card.annotation" class="card-annotation">{{ card.annotation }}</div>
              <div class="card-actions">
                <el-button size="small" text :icon="EditPen">编辑</el-button>
                <el-button size="small" text :icon="Close" @click="deleteCard(card.id)">删除</el-button>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </div>
      
      <div class="footprints-section" v-if="sessionId">
        <FootprintPanel :session-id="sessionId" />
      </div>
    </div>
  </aside>
</template>

<style scoped>
.sidebar-hover {
  position: fixed;
  left: 0;
  top: 0;
  width: 260px;
  height: 100vh;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  z-index: 99;
  transform: translateX(-260px);
  transition: transform var(--transition-normal);
  display: flex;
  flex-direction: column;
  padding-top: 48px;
}

.sidebar-hover.is-visible {
  transform: translateX(0);
}

.sidebar-content {
  flex: 1;
  padding: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: var(--font-size-sm);
  color: var(--text-primary);
}

.section-count {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  background: var(--bg-hover);
  padding: 2px 8px;
  border-radius: 10px;
}

.cards-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-item {
  padding: 10px;
  background: var(--bg-card);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
}

.card-source {
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  line-height: 1.5;
}

.card-annotation {
  font-size: var(--font-size-xs);
  color: var(--text-accent);
  margin-top: 6px;
  padding: 4px 8px;
  background: color-mix(in srgb, var(--text-accent) 15%, transparent);
  border-radius: var(--radius-sm);
}

.card-actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
}

.footprints-section {
  flex: 1;
  min-height: 180px;
}
</style>