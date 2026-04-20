const LATEX_NEWLINE_PLACEHOLDER = '%%LATEX_NEWLINE%%'
const LATEX_DOUBLE_BACKSLASH_PLACEHOLDER = '%%LATEX_DBS%%'
const LATEX_MATRIX_ROW_PLACEHOLDER = '%%LATEX_MATRIX_ROW%%'

export function safeLatexFormat(rawText: string): string {
  const latexRegex = /(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g
  
  return rawText.replace(latexRegex, (match) => {
    let result = match
    
    result = result.replace(/\\\\\\\\/g, LATEX_DOUBLE_BACKSLASH_PLACEHOLDER)
    
    result = result.replace(/\\\\/g, LATEX_NEWLINE_PLACEHOLDER)
    
    return result
  })
}

export function restoreLatexNewlines(renderedHtml: string): string {
  let result = renderedHtml
  
  result = result.replace(new RegExp(LATEX_DOUBLE_BACKSLASH_PLACEHOLDER, 'g'), '\\\\\\\\')
  
  result = result.replace(new RegExp(LATEX_NEWLINE_PLACEHOLDER, 'g'), '\\\\')
  
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
  
  let text = markdown.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
    const placeholder = `%%LATEX_BLOCK_${blocks.length}%%`
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
  
  text = text.replace(/\$([^$]+?)\$/g, (match, formula) => {
    const placeholder = `%%LATEX_INLINE_${blocks.length}%%`
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