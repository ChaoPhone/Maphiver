const LATEX_MATRIX_ROW_PLACEHOLDER = '%%LATEX_MATRIX_ROW%%'

// 占位符必须使用不含 markdown 特殊字符的格式
// 旧格式 %%LATEX_BLOCK_0%% 中的下划线 _ 会被 marked 解析为斜体
// 新格式 %%LATEXBLOCK0%% 不含任何 markdown 特殊字符，marked 不会干扰
const BLOCK_PLACEHOLDER_PREFIX = '%%LATEXBLOCK'
const INLINE_PLACEHOLDER_PREFIX = '%%LATEXINLINE'
const PLACEHOLDER_SUFFIX = '%%'

export function safeLatexFormat(rawText: string): string {
  const latexRegex = /(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g
  
  return rawText.replace(latexRegex, (match) => {
    let result = match
    
    result = result.replace(/\\\\\\\\/g, '%%LATEX_DBS%%')
    
    result = result.replace(/\\\\/g, '%%LATEX_NEWLINE%%')
    
    return result
  })
}

export function restoreLatexNewlines(renderedHtml: string): string {
  let result = renderedHtml
  
  result = result.replace(/%%LATEX_DBS%%/g, '\\\\\\\\')
  
  result = result.replace(/%%LATEX_NEWLINE%%/g, '\\\\')
  
  return result
}

export function preprocessLatexFormula(formula: string): string {
  let processed = formula.trim()
  
  const hasMatrix = /\\begin\{(pmatrix|bmatrix|vmatrix|Vmatrix|matrix|array)\}/.test(processed)

  if (!hasMatrix) {
    processed = processed.replace(/\r\n|\r|\n/g, ' ')
    processed = processed.replace(/\s+/g, ' ')
  } else {
    processed = processed.replace(/\r\n|\r|\n/g, ' ')
    processed = processed.replace(/\s+/g, ' ')
    processed = processed.replace(/\\\\\\\\/g, '\\\\')
    processed = processed.replace(/\\{2,4}/g, '\\\\')
  }

  processed = processed.replace(/\\\\\\\\/g, '\\\\')
  
  return processed
}

function cleanBlockquoteInFormula(formula: string): string {
  const lines = formula.split(/\r?\n/)
  const cleanedLines = lines.map(line => {
    const trimmed = line.trim()
    if (trimmed.startsWith('>')) {
      return trimmed.slice(1).trim()
    }
    return trimmed
  })
  return cleanedLines.join(' ')
}

export function extractLatexBlocks(markdown: string): {
  text: string
  blocks: Array<{ placeholder: string; formula: string; display: boolean }>
} {
  const blocks: Array<{ placeholder: string; formula: string; display: boolean }> = []

  // 处理 \[...\] 块级公式（标准 LaTeX 显示数学语法）
  // 必须在 $$ 之前处理，因为内容格式相同
  let text = markdown.replace(/\\\[([\s\S]*?)\\\]/g, (match, formula) => {
    const placeholder = `${BLOCK_PLACEHOLDER_PREFIX}${blocks.length}${PLACEHOLDER_SUFFIX}`
    const hasMatrix = /\\begin\{(pmatrix|bmatrix|vmatrix|Vmatrix|matrix|array)\}/.test(formula)
    let processedFormula = formula

    processedFormula = cleanBlockquoteInFormula(processedFormula)

    if (hasMatrix) {
      processedFormula = processedFormula.replace(/\\\\/g, LATEX_MATRIX_ROW_PLACEHOLDER)
      processedFormula = preprocessLatexFormula(processedFormula)
      processedFormula = processedFormula.replace(new RegExp(LATEX_MATRIX_ROW_PLACEHOLDER, 'g'), '\\\\')
    } else {
      processedFormula = preprocessLatexFormula(processedFormula)
    }

    blocks.push({ placeholder, formula: processedFormula, display: true })
    return placeholder
  })

  // 处理块级公式 $$...$$
  text = text.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
    const placeholder = `${BLOCK_PLACEHOLDER_PREFIX}${blocks.length}${PLACEHOLDER_SUFFIX}`
    const hasMatrix = /\\begin\{(pmatrix|bmatrix|vmatrix|Vmatrix|matrix|array)\}/.test(formula)
    let processedFormula = formula
    
    processedFormula = cleanBlockquoteInFormula(processedFormula)
    
    if (hasMatrix) {
      processedFormula = processedFormula.replace(/\\\\/g, LATEX_MATRIX_ROW_PLACEHOLDER)
      processedFormula = preprocessLatexFormula(processedFormula)
      processedFormula = processedFormula.replace(new RegExp(LATEX_MATRIX_ROW_PLACEHOLDER, 'g'), '\\\\')
    } else {
      processedFormula = preprocessLatexFormula(processedFormula)
    }
    
    blocks.push({ placeholder, formula: processedFormula, display: true })
    return placeholder
  })
  
  // 处理行内公式 $...$
  // 使用两步法避免误匹配 $$ 块内的内容：
  // 1. 先找出所有 $$ 块的位置范围
  // 2. 再找出所有 $...$ 匹配，排除在 $$ 块内的
  // 这样完全兼容所有浏览器，不需要负向断言
  
  // 找出所有 $$ 块的位置
  const blockDollarPositions: number[] = []
  for (const match of text.matchAll(/\$\$/g)) {
    blockDollarPositions.push(match.index!)
  }
  
  // 配对 $$ 位置，确定块级公式范围
  const blockRanges: Array<{ start: number; end: number }> = []
  for (let i = 0; i < blockDollarPositions.length; i += 2) {
    if (i + 1 < blockDollarPositions.length) {
      blockRanges.push({
        start: blockDollarPositions[i],
        end: blockDollarPositions[i + 1] + 2 // +2 for $$
      })
    }
  }
  
  // 找出所有 $...$ 并排除在块级公式内的
  const inlineMatches: Array<{ match: string; index: number }> = []
  for (const match of text.matchAll(/\$([^$]+?)\$/g)) {
    const pos = match.index!
    const inBlock = blockRanges.some(r => pos >= r.start && pos < r.end)
    if (!inBlock) {
      inlineMatches.push({ match: match[0], index: pos })
    }
  }
  
  // 从后往前替换，避免索引偏移问题
  inlineMatches.reverse().forEach(({ match, index }) => {
    const formula = match.slice(1, -1) // 去掉首尾 $
    const placeholder = `${INLINE_PLACEHOLDER_PREFIX}${blocks.length}${PLACEHOLDER_SUFFIX}`
    const hasMatrix = /\\begin\{(pmatrix|bmatrix|vmatrix|Vmatrix|matrix|array)\}/.test(formula)
    let processedFormula = formula
    
    processedFormula = cleanBlockquoteInFormula(processedFormula)
    
    if (hasMatrix) {
      processedFormula = processedFormula.replace(/\\\\/g, LATEX_MATRIX_ROW_PLACEHOLDER)
      processedFormula = preprocessLatexFormula(processedFormula)
      processedFormula = processedFormula.replace(new RegExp(LATEX_MATRIX_ROW_PLACEHOLDER, 'g'), '\\\\')
    } else {
      processedFormula = preprocessLatexFormula(processedFormula)
    }
    
    blocks.push({ placeholder, formula: processedFormula, display: false })
    
    // 替换 text 中的这个 $...$
    text = text.slice(0, index) + placeholder + text.slice(index + match.length)
  })
  
  return { text, blocks }
}

export function isLatexMatrix(formula: string): boolean {
  const matrixPatterns = [
    /\\begin\{matrix\}/,
    /\\begin\{pmatrix\}/,
    /\\begin\{bmatrix\}/,
    /\\begin\{vmatrix\}/,
    /\\begin\{Vmatrix\}/,
    /\\begin\{array\}/,
  ]
  
  return matrixPatterns.some(pattern => pattern.test(formula))
}

export function validateLatexSyntax(formula: string): string {
  const openBraces = (formula.match(/\{/g) || []).length
  const closeBraces = (formula.match(/\}/g) || []).length
  
  if (openBraces !== closeBraces) {
    return '括号不匹配'
  }
  
  const beginCommands = (formula.match(/\\begin\{/g) || []).length
  const endCommands = (formula.match(/\\end\{/g) || []).length
  
  if (beginCommands !== endCommands) {
    return 'begin/end 不匹配'
  }
  
  return ''
}
