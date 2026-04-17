from openai import OpenAI
from typing import Generator

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from models.schemas import StreamChunk, ChunkType
from utils.exceptions import AIServiceError
from prompts import FORMAT_SYSTEM, FORMAT_PROMPT, QA_SYSTEM_PROMPT, QA_USER_PROMPT, LATEX_FORMAT


client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)


def format_text_with_ai(extracted_text: str) -> str:
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
                {"role": "system", "content": FORMAT_SYSTEM},
                {"role": "user", "content": FORMAT_PROMPT.format(
                    extracted_text=extracted_text,
                    latex_format=LATEX_FORMAT
                )},
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