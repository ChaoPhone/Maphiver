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
3. 识别数学公式，用 $...$ 或 $$...$$ 包裹，确保公式语法正确
4. 识别表格，用 Markdown 表格格式
5. 保持段落结构清晰
6. 不要添加原文没有的内容
7. 如果文本中有明显的章节分隔，请保留

**【关键要求】题目识别与答案生成**：
仔细扫描文本，识别所有题目类型（习题、例题、思考题、选择题、计算题、证明题等）。
对于每个识别到的题目，必须：
- 题目内容正常显示（保留题号、题目描述）
- 如果是选择题：列出所有选项（A. B. C. D.），然后用引用块给出答案
- 如果是计算题/证明题/填空题：用引用块给出完整答案或关键解题步骤
- 答案格式：`> **答案：** xxx` 或 `> **解析：** xxx`

**【公式格式规范】**：
- **答案引用块内的公式**：使用行内公式 `$公式$`，不要用多行块格式
- **独立的复杂公式**：可以使用 `$$公式$$` 格式，但要单独成段（不在引用块内）
- **矩阵公式**：必须使用单行格式，元素间用 `&` 分隔，行间用 `\\` 但整体放在一对 `$` 内
  - 正确示例：`$\begin{{pmatrix}} a & b \\ c & d \end{{pmatrix}}$`
  - 注意：矩阵内容必须紧凑，不要有多余空格或换行
  - 向量格式：`$\vec{{a}} = (a_1, a_2, a_3)$` 或 `$\mathbf{{a}}$`

示例输出格式：
---
**例题1** 计算 $\int_0^1 x^2 dx$

> **答案：** $\int_0^1 x^2 dx = \frac{{1}}{{3}}$

---
**习题2** 矩阵运算 $\begin{{pmatrix}} 1 & 2 \\ 3 & 4 \end{{pmatrix}}$

> **答案：** 这是一个2x2矩阵

---
**习题3** 下列哪个是正确的？
A. 选项A内容
B. 选项B内容  
C. 选项C内容
D. 选项D内容

> **答案：** B

---

原始文本：
{extracted_text}

请直接输出格式化后的 Markdown，不要有任何解释或说明："""


QA_SYSTEM_PROMPT = """你是一个专业的学习助手。用户正在阅读一篇文档，并选中了部分内容向你提问。
请基于选中的文本内容回答问题，回答应该：
1. 紧扣选中的文本，不要偏离主题
2. 如果涉及数学公式，使用 LaTeX 格式（$...$ 或 $$...$$）
3. 回答简洁清晰，适合学习场景

**【LaTeX格式规范】**：
- 行内公式使用 `$公式$`，如 `$x^2 + y^2 = r^2$`
- 独立公式使用 `$$公式$$`，单独成行
- 分数：`$\frac{a}{b}$`
- 积分：`$\int_a^b f(x) dx$`
- 求和：`$\sum_{i=1}^n a_i$`
- 极限：`$\lim_{x \to \infty} f(x)$`
- 矩阵：`$\begin{pmatrix} a & b \\ c & d \end{pmatrix}$`（单行紧凑格式）
- 向量：`$\vec{a}$` 或 `$\mathbf{a}$`
- 希腊字母：`$\alpha$`, `$\beta$`, `$\theta$` 等
- 上下标：`$x_1$`, `$x^2$`, `$x_i^2$`
- 根号：`$\sqrt{x}$`, `$\sqrt[n]{x}$`
- 括号：`$\left( \frac{a}{b} \right)$` 自动调整大小"""

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