import uuid
from datetime import datetime
from typing import Generator, Optional, List

from models.schemas import Message, MessageRole, StreamChunk, ContentBlock
from repositories.database import MessageRepository
from services.ai_service import stream_qa_answer


QUICK_QUESTIONS = {
    "详细": "请详细展开这个概念，解释其含义和重要性。",
    "简化": "请用最简洁的语言总结这个概念的核心要点。",
    "类比": "请用一个类比或比喻来帮助理解这个概念。",
    "举例": "请举一个具体的例子来说明这个概念的应用。",
}


def find_block_by_text(blocks: List[ContentBlock], selected_text: str) -> Optional[str]:
    if not blocks or not selected_text:
        return None
    
    selected_text_clean = selected_text.strip()
    
    for block in blocks:
        if selected_text_clean in block.content:
            return block.id
    
    return None


def get_context_blocks(
    blocks: List[ContentBlock],
    selected_block_id: Optional[str],
    selected_text: Optional[str] = None,
) -> str:
    if not blocks:
        return ""
    
    if not selected_block_id and selected_text:
        selected_block_id = find_block_by_text(blocks, selected_text)
    
    if not selected_block_id:
        if selected_text:
            return selected_text
        return ""
    
    block_index = -1
    for i, block in enumerate(blocks):
        if block.id == selected_block_id:
            block_index = i
            break
    
    if block_index == -1:
        if selected_text:
            return selected_text
        return ""
    
    start_index = max(0, block_index - 1)
    end_index = min(len(blocks), block_index + 2)
    
    context_parts = []
    for i in range(start_index, end_index):
        prefix = "【上文】" if i < block_index else ("【选中】" if i == block_index else "【下文】")
        context_parts.append(f"{prefix}\n{blocks[i].content}")
    
    return "\n\n---\n\n".join(context_parts)


def ask_question(
    session_id: str,
    question: str,
    selected_text: Optional[str] = None,
    block_id: Optional[str] = None,
) -> Message:
    message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=MessageRole.USER,
        content=question,
        block_id=block_id,
        created_at=datetime.now(),
    )
    
    return MessageRepository.create(message)


def save_answer(
    session_id: str,
    content: str,
    block_id: Optional[str] = None,
) -> Message:
    message = Message(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=content,
        block_id=block_id,
        created_at=datetime.now(),
    )
    
    return MessageRepository.create(message)


def stream_answer(
    session_id: str,
    question: str,
    selected_text: str,
    context_text: str,
    block_id: Optional[str] = None,
) -> Generator[StreamChunk, None, None]:
    ask_question(session_id, question, selected_text, block_id)
    
    full_content = ""
    
    for chunk in stream_qa_answer(selected_text, context_text, question):
        if chunk.type.value == "text":
            full_content += chunk.content or ""
            yield chunk
        elif chunk.type.value == "done":
            if full_content:
                save_answer(session_id, full_content, block_id)
            yield chunk
        elif chunk.type.value == "error":
            yield chunk


def get_messages(session_id: str) -> List[Message]:
    return MessageRepository.list_by_session(session_id)


def get_quick_question(question_type: str) -> Optional[str]:
    return QUICK_QUESTIONS.get(question_type)