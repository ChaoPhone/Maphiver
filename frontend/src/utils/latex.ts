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
  
  // 先处理块级公式 $$...$$
  let text = markdown.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
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
  // 关键修复：排除 $$ 的情况，并使用更精确的正则
  // 使用否定后行断言确保不以 $ 开头，否定先行断言确保不以 $ 结尾
  // 这样可以避免误匹配 $$ 中的内容
  text = text.replace(/(?<!\$)\$(?!\$)([^\$]+?)\$(?!\$)/g, (match, formula) => {
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
    return placeholder
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
