import type { QAMessage } from '@/types'

/**
 * 查找与block文本相关的QA消息
 * @param blockText block元素的文本内容
 * @param qaMessages QA消息列表
 * @returns 匹配的QA消息数组
 */
export function findRelatedQA(blockText: string, qaMessages: QAMessage[] | undefined): QAMessage[] {
  if (!qaMessages || qaMessages.length === 0) return []

  const blockLower = blockText.toLowerCase().trim()
  if (!blockLower) return []

  return qaMessages.filter(msg => {
    const selectedLower = (msg.selected_text || '').toLowerCase().trim()

    if (!selectedLower) return false

    // 匹配策略1：选中文本完全包含在block中
    if (blockLower.includes(selectedLower)) return true

    // 匹配策略2：block完全包含在选中文本中
    if (selectedLower.includes(blockLower)) return true

    // 匹配策略3：选中文本的任何部分（至少3字符）出现在block中
    const minMatchLen = Math.min(3, selectedLower.length)
    for (let i = 0; i <= selectedLower.length - minMatchLen; i++) {
      const slice = selectedLower.slice(i, i + minMatchLen)
      if (slice.length >= minMatchLen && blockLower.includes(slice)) return true
    }

    // 匹配策略4：block的前50字符出现在选中文本中
    if (blockLower.length >= 50 && selectedLower.includes(blockLower.slice(0, 50))) return true

    return false
  })
}