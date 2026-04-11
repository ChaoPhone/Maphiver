from openai import OpenAI
from typing import Generator

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from models.schemas import StreamChunk, ChunkType
from utils.exceptions import AIServiceError


client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)


FORMAT_PROMPT = """你是一个文档格式化助手。请将以下从 PDF 提取的纯文本转换为结构化的 Markdown 格式。

要求：
1. 识别标题层级（#, ##, ###），根据字体大小和上下文判断
2. 识别列表项（- 或 1. 2. 3.）
3. 识别数学公式，用 $...$ 或 $$...$$ 包裹
4. 识别表格，用 Markdown 表格格式
5. 保持段落结构清晰
6. 不要添加原文没有的内容
7. 如果文本中有明显的章节分隔，请保留
8. **重要**：如果内容中存在题目（如习题、例题、思考题等），请在题目下方用引用格式（> ）给出答案或解析。格式如下：
   - 题目正常显示
   - 答案用 `> **答案/解析：**` 开头，后接答案内容
   - 如果是选择题，列出选项并标注正确答案
   - 如果是计算题/证明题，给出关键步骤

原始文本：
{extracted_text}

请直接输出格式化后的 Markdown，不要有任何解释或说明："""


QA_SYSTEM_PROMPT = """你是一个专业的学习助手。用户正在阅读一篇文档，并选中了部分内容向你提问。
请基于选中的文本内容回答问题，回答应该：
1. 紧扣选中的文本，不要偏离主题
2. 如果涉及数学公式，使用 LaTeX 格式（$...$ 或 $$...$$）
3. 回答简洁清晰，适合学习场景"""

QA_USER_PROMPT = """选中的文本及上下文：
{context_text}

用户选中的具体内容：
{selected_text}

问题：{question}"""


def format_text_with_ai(extracted_text: str) -> str:
    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的文档格式化助手，擅长将纯文本转换为结构化的 Markdown 格式。"},
                {"role": "user", "content": FORMAT_PROMPT.format(extracted_text=extracted_text)},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        return response.choices[0].message.content
        
    except Exception as e:
        raise AIServiceError(f"AI 格式化失败: {str(e)}")


def format_text_stream(extracted_text: str) -> Generator[StreamChunk, None, None]:
    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的文档格式化助手，擅长将纯文本转换为结构化的 Markdown 格式。"},
                {"role": "user", "content": FORMAT_PROMPT.format(extracted_text=extracted_text)},
            ],
            temperature=0.3,
            max_tokens=4000,
            stream=True,
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield StreamChunk(
                    type=ChunkType.TEXT,
                    content=chunk.choices[0].delta.content,
                )
        
        yield StreamChunk(type=ChunkType.DONE)
        
    except Exception as e:
        yield StreamChunk(
            type=ChunkType.ERROR,
            error_message=str(e),
        )


def stream_qa_answer(
    selected_text: str,
    context_text: str,
    question: str,
) -> Generator[StreamChunk, None, None]:
    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": QA_SYSTEM_PROMPT},
                {"role": "user", "content": QA_USER_PROMPT.format(
                    context_text=context_text,
                    selected_text=selected_text,
                    question=question,
                )},
            ],
            temperature=0.7,
            max_tokens=2000,
            stream=True,
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield StreamChunk(
                    type=ChunkType.TEXT,
                    content=chunk.choices[0].delta.content,
                )
        
        yield StreamChunk(type=ChunkType.DONE)
        
    except Exception as e:
        yield StreamChunk(
            type=ChunkType.ERROR,
            error_message=str(e),
        )