from openai import OpenAI
import httpx
from typing import Generator

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from models.schemas import StreamChunk, ChunkType
from utils.exceptions import AIServiceError
from prompts import FORMAT_SYSTEM, FORMAT_PROMPT, QA_SYSTEM_PROMPT, QA_USER_PROMPT, LATEX_FORMAT


client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
    timeout=httpx.Timeout(120.0, connect=15.0, read=60.0),
)

# ── 各场景输出 token 上限 ──────────────────────────────────
MAX_TOKENS_FORMAT = 32000     # 文档格式化
MAX_TOKENS_QA = 8000          # QA 问答


def format_text_with_ai(extracted_text: str) -> str:
    """
    使用 AI 格式化文本（非流式）
    DeepSeek V4.0 Flash / 关闭思考模式 / 最大 32K 输出

    Args:
        extracted_text: 待格式化的原始文本

    Returns:
        格式化后的 Markdown 文本

    Raises:
        AIServiceError: AI 服务调用失败
    """
    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": FORMAT_SYSTEM},
                {"role": "user", "content": FORMAT_PROMPT.format(
                    extracted_text=extracted_text,
                    latex_format=LATEX_FORMAT
                )},
            ],
            temperature=0.3,
            max_tokens=MAX_TOKENS_FORMAT,
            extra_body={"thinking": {"type": "disabled"}},
        )
        return response.choices[0].message.content

    except Exception as e:
        raise AIServiceError(f"AI 格式化失败: {str(e)}")


def format_text_stream(extracted_text: str) -> Generator[StreamChunk, None, None]:
    """
    使用 AI 流式格式化文本
    DeepSeek V4.0 Flash / 关闭思考模式 / 最大 32K 输出

    Args:
        extracted_text: 待格式化的原始文本

    Yields:
        StreamChunk: 流式输出的内容块
    """
    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": FORMAT_SYSTEM},
                {"role": "user", "content": FORMAT_PROMPT.format(
                    extracted_text=extracted_text,
                    latex_format=LATEX_FORMAT
                )},
            ],
            temperature=0.3,
            max_tokens=MAX_TOKENS_FORMAT,
            extra_body={"thinking": {"type": "disabled"}},
            stream=True,
            stream_options={"include_usage": True},  # 流式结束返回 token 用量
        )

        for chunk in response:
            if not chunk.choices:
                continue  # skip usage-only chunk
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield StreamChunk(
                    type=ChunkType.TEXT,
                    content=delta.content,
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
    """
    流式 QA 回答
    DeepSeek V4.0 Flash / 开启思考模式 / 推理强度 high / 最大 8K 输出

    Args:
        selected_text: 用户选中的文本
        context_text: 上下文文本
        question: 用户提问

    Yields:
        StreamChunk: 流式输出的内容块
    """
    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": QA_SYSTEM_PROMPT.format(
                    latex_format=LATEX_FORMAT
                )},
                {"role": "user", "content": QA_USER_PROMPT.format(
                    context_text=context_text,
                    selected_text=selected_text,
                    question=question,
                )},
            ],
            temperature=0.7,
            max_tokens=MAX_TOKENS_QA,
            reasoning_effort="high",
            extra_body={
                "thinking": {"type": "enabled"},
            },
            stream=True,
            stream_options={"include_usage": True},  # 流式结束返回 token 用量
        )

        for chunk in response:
            if not chunk.choices:
                continue  # skip usage-only chunk
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield StreamChunk(
                    type=ChunkType.TEXT,
                    content=delta.content,
                )

        yield StreamChunk(type=ChunkType.DONE)

    except Exception as e:
        yield StreamChunk(
            type=ChunkType.ERROR,
            error_message=str(e),
        )
