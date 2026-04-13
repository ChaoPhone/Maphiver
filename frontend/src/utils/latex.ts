const LATEX_NEWLINE_PLACEHOLDER = '%%LATEX_NEWLINE%%'
const LATEX_DOUBLE_BACKSLASH_PLACEHOLDER = '%%LATEX_DBS%%'

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
  
  processed = processed.replace(/\r\n|\r|\n/g, ' ')
  
  processed = processed.replace(/\s+/g, ' ')
  
  processed = processed.replace(/\\\\\\\\/g, '\\\\')
  
  return processed
}

export function extractLatexBlocks(markdown: string): {
  text: string
  blocks: Array<{ placeholder: string; formula: string; display: boolean }>
} {
  const blocks: Array<{ placeholder: string; formula: string; display: boolean }> = []
  
  let text = markdown.replace(/\$\$([\s\S]+?)\$\$/g, (match, formula) => {
    const placeholder = `%%LATEX_BLOCK_${blocks.length}%%`
    const processedFormula = preprocessLatexFormula(formula)
    blocks.push({ placeholder, formula: processedFormula, display: true })
    return placeholder
  })
  
  text = text.replace(/\$([^$\n]+?)\$/g, (match, formula) => {
    const placeholder = `%%LATEX_INLINE_${blocks.length}%%`
    const processedFormula = preprocessLatexFormula(formula)
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

export function validateLatexSyntax(formula: string): { valid: boolean; error?: string } {
  const openBraces = (formula.match(/\{/g) || []).length
  const closeBraces = (formula.match(/\}/g) || []).length
  
  if (openBraces !== closeBraces) {
    return { valid: false, error: '括号不匹配' }
  }
  
  const beginCommands = (formula.match(/\\begin\{/g) || []).length
  const endCommands = (formula.match(/\\end\{/g) || []).length
  
  if (beginCommands !== endCommands) {
    return { valid: false, error: 'begin/end 不匹配' }
  }
  
  return { valid: true }
}