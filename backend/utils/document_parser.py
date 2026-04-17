import fitz
from typing import List, Tuple
from pathlib import Path
import base64
import hashlib
import os

from models.schemas import ContentBlock
from utils.exceptions import ParseError
from config import DATA_DIR


IMAGES_DIR = DATA_DIR / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def _save_image(image_bytes: bytes, doc_hash: str, image_index: int, image_ext: str = "png") -> str:
    # 统一图片格式后缀，去掉多余的点
    if image_ext.startswith('.'):
        image_ext = image_ext[1:]
    image_ext = image_ext.lower() or "png"
    
    # 只保留常见图片格式，未知格式默认png
    allowed_exts = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
    if image_ext not in allowed_exts:
        image_ext = "png"
    
    image_filename = f"{doc_hash}_img_{image_index}.{image_ext}"
    image_path = IMAGES_DIR / image_filename
    
    with open(image_path, "wb") as f:
        f.write(image_bytes)
    
    return f"/api/images/{image_filename}"


def extract_text_from_pdf(pdf_path: str) -> Tuple[str, int, List[ContentBlock]]:
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        blocks = []
        full_text = ""
        
        doc_hash = hashlib.md5(Path(pdf_path).name.encode()).hexdigest()[:8]
        image_index = 0
        
        for page_num in range(total_pages):
            page = doc[page_num]
            
            # 获取页面所有元素（文本块+图片），按y坐标排序
            page_elements = []
            
            # 先获取文本块
            text_blocks = page.get_text("dict")["blocks"]
            for b in text_blocks:
                if b["type"] == 0:  # 文本块
                    text_content = ""
                    for line in b["lines"]:
                        for span in line["spans"]:
                            text_content += span["text"]
                        text_content += "\n"
                    if text_content.strip():
                        page_elements.append({
                            "type": "text",
                            "y": b["bbox"][1],  # 上边界y坐标
                            "content": text_content.strip()
                        })
            
            # 再获取图片块
            image_list = page.get_images(full=True)
            for img_info in image_list:
                xref = img_info[0]
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image.get("ext", "png")
                    
                    # 获取图片位置
                    img_rects = page.get_image_rects(xref)
                    if img_rects:
                        y_pos = img_rects[0][1]  # 图片上边界y坐标
                    else:
                        y_pos = 99999  # 未知位置放最后
                    
                    if len(image_bytes) > 1000:
                        image_index += 1
                        image_url = _save_image(image_bytes, doc_hash, image_index, image_ext)
                        md_content = f"![图片 {image_index}]({image_url})"
                        
                        page_elements.append({
                            "type": "image",
                            "y": y_pos,
                            "content": md_content,
                            "image_path": image_url,
                            "image_id": f"img_{page_num + 1}_{image_index}"
                        })
                except Exception:
                    pass
            
            # 按y坐标从小到大排序，保证从上到下的顺序
            page_elements.sort(key=lambda x: x["y"])
            
            # 处理页面标题
            full_text += f"\n--- 第 {page_num + 1} 页 ---\n"
            
            # 按顺序添加元素
            for elem in page_elements:
                if elem["type"] == "text":
                    full_text += elem["content"] + "\n\n"
                    blocks.append(ContentBlock(
                        id=f"page_{page_num + 1}_{len(blocks)}",
                        type="page",
                        page=page_num + 1,
                        content=elem["content"],
                    ))
                elif elem["type"] == "image":
                    full_text += elem["content"] + "\n\n"
                    blocks.append(ContentBlock(
                        id=elem["image_id"],
                        type="image",
                        page=page_num + 1,
                        content=elem["content"],
                        image_path=elem["image_path"],
                    ))
        
        doc.close()
        return full_text.strip(), total_pages, blocks
        
    except Exception as e:
        raise ParseError(f"PDF 文本提取失败: {str(e)}")


def extract_text_from_docx(docx_path: str) -> Tuple[str, int, List[ContentBlock]]:
    try:
        from docx import Document
        
        doc = Document(docx_path)
        blocks = []
        full_text = ""
        paragraph_count = 0
        
        doc_hash = hashlib.md5(Path(docx_path).name.encode()).hexdigest()[:8]
        image_index = 0
        
        image_rels = {}
        for rel in doc.part.rels.values():
            if "image" in rel.reltype:
                image_rels[rel.rId] = rel.target_part.blob
        
        for para in doc.paragraphs:
            text = para.text.strip()
            
            # 先处理段落中的图片
            para_images = []
            for run in para.runs:
                run_xml = run._element.xml
                if 'drawing' in run_xml or 'blip' in run_xml:
                    import re
                    rIds = re.findall(r'r:embed="([^"]+)"', run_xml)
                    for rId in rIds:
                        if rId in image_rels:
                            image_bytes = image_rels[rId]
                            if len(image_bytes) > 1000:
                                # 识别图片格式
                                if image_bytes.startswith(b'\xff\xd8\xff'):
                                    image_ext = "jpg"
                                elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
                                    image_ext = "png"
                                elif image_bytes.startswith(b'GIF89a') or image_bytes.startswith(b'GIF87a'):
                                    image_ext = "gif"
                                else:
                                    image_ext = "png"
                                
                                image_index += 1
                                image_url = _save_image(image_bytes, doc_hash, image_index, image_ext)
                                
                                blocks.append(ContentBlock(
                                    id=f"img_{image_index}",
                                    type="image",
                                    page=1,
                                    content=f"![图片 {image_index}]({image_url})",
                                    image_path=image_url,
                                ))
                                
                                para_images.append(f"\n![图片 {image_index}]({image_url})\n")
            
            # 如果段落有文本，先加文本，然后加图片
            if text:
                full_text += text + "\n\n"
                paragraph_count += 1
                blocks.append(ContentBlock(
                    id=f"para_{paragraph_count}",
                    type="paragraph",
                    page=1,
                    content=text,
                ))
            
            # 添加段落中的图片
            for img_md in para_images:
                full_text += img_md
        
        for table in doc.tables:
            table_text = ""
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells)
                table_text += row_text + "\n"
            
            if table_text.strip():
                full_text += "\n[TABLE]\n" + table_text + "\n"
                blocks.append(ContentBlock(
                    id=f"table_{len(blocks) + 1}",
                    type="table",
                    page=1,
                    content=table_text.strip(),
                ))
        
        return full_text.strip(), 1, blocks
        
    except ImportError:
        raise ParseError("需要安装 python-docx 库来处理 docx 文件")
    except Exception as e:
        raise ParseError(f"DOCX 文本提取失败: {str(e)}")


def extract_text_from_doc(doc_path: str) -> Tuple[str, int, List[ContentBlock]]:
    try:
        import subprocess
        import tempfile
        
        docx_path = Path(doc_path).with_suffix('.docx')
        
        try:
            subprocess.run([
                'soffice', '--headless', '--convert-to', 'docx',
                '--outdir', str(Path(doc_path).parent),
                str(doc_path)
            ], check=True, capture_output=True, timeout=60)
            
            if docx_path.exists():
                result = extract_text_from_docx(str(docx_path))
                try:
                    docx_path.unlink()
                except:
                    pass
                return result
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        except FileNotFoundError:
            pass
        
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            
            doc = word.Documents.Open(str(Path(doc_path).absolute()))
            full_text = doc.Content.Text
            doc.Close(False)
            word.Quit()
            
            blocks = []
            paragraphs = full_text.split('\n')
            for i, para in enumerate(paragraphs):
                if para.strip():
                    blocks.append(ContentBlock(
                        id=f"para_{i + 1}",
                        type="paragraph",
                        page=1,
                        content=para.strip(),
                    ))
            
            return full_text.strip(), 1, blocks
            
        except ImportError:
            raise ParseError("需要安装 pywin32 库或 LibreOffice 来处理 doc 文件")
        
    except Exception as e:
        raise ParseError(f"DOC 文本提取失败: {str(e)}")


def extract_text_from_document(file_path: str) -> Tuple[str, int, List[ContentBlock]]:
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.doc':
        return extract_text_from_doc(file_path)
    else:
        raise ParseError(f"不支持的文件格式: {ext}")