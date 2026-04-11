import fitz
from pathlib import Path
from typing import List, Tuple

from models.schemas import ContentBlock, ParseResult
from utils.exceptions import ParseError


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, int, List[ContentBlock]]:
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        blocks = []
        full_text = ""
        
        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text("text")
            full_text += f"\n--- Page {page_num + 1} ---\n"
            full_text += text
            
            if text.strip():
                blocks.append(ContentBlock(
                    id=f"page_{page_num + 1}",
                    type="page",
                    page=page_num + 1,
                    content=text.strip(),
                ))
        
        doc.close()
        return full_text, total_pages, blocks
        
    except Exception as e:
        raise ParseError(f"PDF 文本提取失败: {str(e)}")


def parse_pdf_to_text(pdf_path: str, document_id: str) -> ParseResult:
    full_text, total_pages, blocks = extract_text_from_pdf(pdf_path)
    
    return ParseResult(
        document_id=document_id,
        blocks=blocks,
        total_pages=total_pages,
        raw_markdown=full_text,
    )