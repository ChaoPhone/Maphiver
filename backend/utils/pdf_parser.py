import fitz
from typing import List, Tuple
import re

from models.schemas import ContentBlock
from utils.exceptions import ParseError


def convert_path_to_wsl(path: str) -> str:
    """将 Windows 路径转换为 WSL 路径"""
    # 匹配 Windows 路径格式，如 E:\project\... -> /mnt/e/project/...
    match = re.match(r'^([A-Za-z]):\\(.*)$', path)
    if match:
        drive = match.group(1).lower()
        rest = match.group(2).replace('\\', '/')
        return f'/mnt/{drive}/{rest}'
    return path


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, int, List[ContentBlock]]:
    try:
        # 转换 Windows 路径为 WSL 路径
        actual_path = convert_path_to_wsl(pdf_path)
        doc = fitz.open(actual_path)
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