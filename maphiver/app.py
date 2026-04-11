import streamlit as st
from datetime import datetime

from config import MAX_UPLOAD_SIZE_MB
from repositories.database import init_db_sync
from services import (
    upload_document,
    parse_document,
    parse_document_stream,
    get_document,
    create_session,
    get_session,
    list_sessions,
    archive_session,
    stream_answer,
    get_quick_question,
    get_context_blocks,
    find_block_by_text,
    record_footprint,
    get_footprints,
)
from models.schemas import ChunkType, ContentBlock
from utils.exceptions import MaphiverError


def init_session_state():
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    if "current_document_id" not in st.session_state:
        st.session_state.current_document_id = None
    if "page_stage" not in st.session_state:
        st.session_state.page_stage = "idle"
    if "selected_text" not in st.session_state:
        st.session_state.selected_text = ""
    if "selected_block_id" not in st.session_state:
        st.session_state.selected_block_id = None
    if "parsed_blocks" not in st.session_state:
        st.session_state.parsed_blocks = []
    if "qa_comments" not in st.session_state:
        st.session_state.qa_comments = []
    if "parse_progress" not in st.session_state:
        st.session_state.parse_progress = 0
    if "parsed_content" not in st.session_state:
        st.session_state.parsed_content = None
    if "total_pages" not in st.session_state:
        st.session_state.total_pages = 0
    if "streaming_answer" not in st.session_state:
        st.session_state.streaming_answer = ""
    if "is_streaming" not in st.session_state:
        st.session_state.is_streaming = False


def handle_error(error: Exception):
    if isinstance(error, MaphiverError):
        st.error(f"❌ {error.message}")
    else:
        st.error("发生未知错误")
        st.exception(error)


def render_top_bar():
    col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
    
    with col1:
        st.markdown("### 📚 Maphiver")
    
    with col2:
        if st.session_state.current_session_id:
            session = get_session(st.session_state.current_session_id)
            if session:
                status_icon = "📝" if session.status.value == "draft" else "📦"
                st.markdown(f"**会话状态:** {status_icon} {session.status.value}")
    
    with col3:
        if st.session_state.page_stage == "ready":
            if st.button("汇入知识河", type="primary", use_container_width=True):
                try:
                    archive_session(st.session_state.current_session_id)
                    st.session_state.page_stage = "idle"
                    st.session_state.current_session_id = None
                    st.session_state.parsed_content = None
                    st.session_state.qa_comments = []
                    st.success("✅ 已归档到知识河")
                    st.rerun()
                except Exception as e:
                    handle_error(e)
    
    with col4:
        st.markdown(f"**阶段:** `{st.session_state.page_stage}`")


def render_left_panel():
    st.markdown("### 📁 知识档案")
    
    if st.session_state.page_stage == "idle":
        st.info("暂无活跃会话")
        st.markdown("---")
        st.markdown("**历史会话**")
        archived_sessions = list_sessions()
        if archived_sessions:
            for session in archived_sessions[:5]:
                doc = get_document(session.document_id)
                if doc:
                    with st.container():
                        st.markdown(f"- 📦 {doc.filename}")
                        st.caption(f"更新: {session.updated_at.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.markdown("*暂无历史会话*")
    
    elif st.session_state.page_stage in ["parsing", "ready"]:
        if st.session_state.current_document_id:
            doc = get_document(st.session_state.current_document_id)
            if doc:
                st.markdown("**当前文档**")
                st.markdown(f"- 📄 **{doc.filename}**")
                if st.session_state.total_pages:
                    st.markdown(f"- 页数: {st.session_state.total_pages}")
                if doc.parsed_at:
                    st.markdown(f"- 解析时间: {doc.parsed_at.strftime('%H:%M:%S')}")
        
        st.markdown("---")
        st.markdown("**会话信息**")
        if st.session_state.current_session_id:
            session = get_session(st.session_state.current_session_id)
            if session:
                st.markdown(f"- 问答数: {len(st.session_state.qa_comments)}")
                st.markdown(f"- 状态: {session.status.value}")
        
        st.markdown("---")
        st.markdown("**最近知识卡**")
        st.info("暂无知识卡片")


def render_center_panel():
    st.markdown("### 📖 阅读核心区")
    
    if st.session_state.page_stage == "idle":
        st.markdown("**初始化阶段 - 上传文档**")
        st.markdown(f"支持 PDF 格式，最大 {MAX_UPLOAD_SIZE_MB}MB")
        
        uploaded_file = st.file_uploader(
            "上传 PDF 文档",
            type=["pdf"],
            key="pdf_uploader",
            help="上传后将自动解析并进入阅读模式",
        )
        
        if uploaded_file is not None:
            if st.button("解析并进入阅读", type="primary", use_container_width=True):
                try:
                    with st.spinner("正在上传..."):
                        document = upload_document(
                            uploaded_file.getvalue(),
                            uploaded_file.name,
                        )
                    st.session_state.current_document_id = document.id
                    st.session_state.page_stage = "parsing"
                    st.session_state.parse_progress = 0
                    st.rerun()
                except Exception as e:
                    handle_error(e)
    
    elif st.session_state.page_stage == "parsing":
        st.markdown("**正在解析文档...**")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        content_preview = st.empty()
        
        try:
            progress_bar.progress(5)
            status_text.markdown("⏳ 正在提取 PDF 文本...")
            
            formatted_content = ""
            
            for chunk in parse_document_stream(st.session_state.current_document_id):
                if chunk.type == ChunkType.TEXT:
                    if chunk.metadata:
                        stage = chunk.metadata.get("stage", "")
                        if stage == "extracting":
                            progress_bar.progress(10)
                            status_text.markdown("⏳ 正在提取 PDF 文本...")
                        elif stage == "extracted":
                            progress_bar.progress(30)
                            total_pages = chunk.metadata.get("total_pages", 0)
                            st.session_state.total_pages = total_pages
                            status_text.markdown(f"⏳ 已提取 {total_pages} 页，正在调用 AI 格式化...")
                        elif stage == "formatting":
                            progress_bar.progress(35)
                            status_text.markdown("⏳ AI 正在格式化文档...")
                        elif stage == "streaming":
                            progress_bar.progress(50)
                            formatted_content += chunk.content or ""
                            content_preview.markdown(formatted_content)
                    else:
                        formatted_content += chunk.content or ""
                        content_preview.markdown(formatted_content)
                        
                elif chunk.type == ChunkType.DONE:
                    progress_bar.progress(90)
                    status_text.markdown("⏳ 处理解析结果...")
                    
                    if chunk.metadata:
                        st.session_state.parsed_content = chunk.metadata.get("raw_markdown", "")
                        st.session_state.total_pages = chunk.metadata.get("total_pages", 0)
                        
                        blocks_data = chunk.metadata.get("blocks", [])
                        st.session_state.parsed_blocks = [
                            ContentBlock(**b) for b in blocks_data
                        ]
                    
                    session = create_session(st.session_state.current_document_id)
                    st.session_state.current_session_id = session.id
                    
                    progress_bar.progress(100)
                    status_text.markdown("✅ 解析完成！")
                    content_preview.empty()
                    
                    st.session_state.page_stage = "ready"
                    st.session_state.qa_comments = []
                    st.rerun()
                    
                elif chunk.type == ChunkType.ERROR:
                    progress_bar.progress(0)
                    status_text.markdown(f"❌ 解析失败: {chunk.error_message}")
                    st.session_state.page_stage = "idle"
                    break
                    
        except Exception as e:
            progress_bar.progress(0)
            status_text.markdown("❌ 解析失败")
            handle_error(e)
    
    elif st.session_state.page_stage == "ready":
        st.markdown("**文档内容**")
        st.markdown("*复制文档中的文本，粘贴到下方输入框进行提问*")
        
        if st.session_state.parsed_content:
            st.markdown(st.session_state.parsed_content)
        else:
            st.info("暂无解析内容")
        
        st.markdown("---")
        
        st.markdown("**📝 选中文本提问**")
        st.markdown("复制文档中的文本段落，粘贴到下方：")
        
        selected_text = st.text_area(
            "选中的文本",
            value=st.session_state.selected_text,
            height=100,
            key="text_selector",
            placeholder="在此粘贴或输入文档中的文本...",
        )
        
        st.session_state.selected_text = selected_text
        
        if selected_text.strip():
            st.markdown("**快捷提问**")
            quick_cols = st.columns(4)
            
            quick_types = ["详细", "简化", "类比", "举例"]
            for i, q_type in enumerate(quick_types):
                if quick_cols[i].button(q_type, use_container_width=True, key=f"quick_{q_type}"):
                    question = get_quick_question(q_type)
                    if question:
                        handle_question(selected_text, question)
        
        st.markdown("**自由提问**")
        free_question = st.text_input(
            "输入你的问题",
            key="free_question",
            placeholder="例如：这个定理有什么应用？",
        )
        
        if st.button("向 AI 提问", type="primary", use_container_width=True) and free_question:
            handle_question(selected_text, free_question)


def handle_question(selected_text: str, question: str):
    if not selected_text.strip():
        st.warning("请先选中文本")
        return
    
    if not st.session_state.current_session_id:
        st.warning("请先上传并解析文档")
        return
    
    context_text = get_context_blocks(
        st.session_state.parsed_blocks,
        st.session_state.selected_block_id,
        selected_text,
    )
    
    if not context_text:
        context_text = selected_text
    
    st.session_state.is_streaming = True
    st.session_state.streaming_answer = ""
    
    display_text = selected_text[:200] + "..." if len(selected_text) > 200 else selected_text
    
    comment = {
        "selected_text": display_text,
        "full_selected_text": selected_text,
        "question": question,
        "answer": "",
        "is_expanded": True,
    }
    st.session_state.qa_comments.append(comment)
    
    record_footprint(
        st.session_state.current_session_id,
        "qa_start",
        {"question": question},
    )
    
    st.rerun()


def truncate_text_for_display(text: str, max_lines: int = 5) -> tuple:
    lines = text.split('\n')
    if len(lines) <= max_lines:
        return text, False
    truncated = '\n'.join(lines[:max_lines])
    return truncated, True


def render_qa_comments():
    st.markdown("### 💬 文档问答")
    st.markdown("<style>.qa-comment { border-left: 3px solid #4CAF50; padding-left: 10px; margin-bottom: 15px; }</style>", unsafe_allow_html=True)
    
    if not st.session_state.qa_comments:
        st.info("暂无问答记录，选中文本后点击提问按钮开始")
        return
    
    for i, comment in enumerate(st.session_state.qa_comments):
        with st.container():
            st.markdown(f"<div class='qa-comment'>", unsafe_allow_html=True)
            
            question_preview = comment['question'][:30] + "..." if len(comment['question']) > 30 else comment['question']
            
            selected_display, needs_expand = truncate_text_for_display(comment['selected_text'], max_lines=4)
            
            if needs_expand:
                with st.expander(f"📝 **选中文本** (点击展开完整内容)", expanded=False):
                    st.markdown(f"> {comment['full_selected_text']}")
            else:
                st.markdown(f"📝 **选中文本:**")
                st.markdown(f"> {selected_display}")
            
            st.markdown(f"❓ **问题:** {comment['question']}")
            
            st.markdown("🤖 **回答:**")
            
            if i == len(st.session_state.qa_comments) - 1 and st.session_state.is_streaming:
                answer_placeholder = st.empty()
                full_answer = ""
                
                context_text = get_context_blocks(
                    st.session_state.parsed_blocks,
                    st.session_state.selected_block_id,
                    comment['full_selected_text'],
                )
                if not context_text:
                    context_text = comment['full_selected_text']
                
                for chunk in stream_answer(
                    st.session_state.current_session_id,
                    comment['question'],
                    comment['full_selected_text'],
                    context_text,
                ):
                    if chunk.type == ChunkType.TEXT:
                        full_answer += chunk.content or ""
                        answer_display, answer_needs_expand = truncate_text_for_display(full_answer, max_lines=5)
                        if answer_needs_expand:
                            answer_placeholder.markdown(f"{answer_display}\n\n*(回答较长，完成后可展开查看完整内容)*")
                        else:
                            answer_placeholder.markdown(full_answer)
                    elif chunk.type == ChunkType.DONE:
                        comment['answer'] = full_answer
                        st.session_state.is_streaming = False
                        record_footprint(
                            st.session_state.current_session_id,
                            "qa_complete",
                            {"question": comment['question']},
                        )
                        st.rerun()
                    elif chunk.type == ChunkType.ERROR:
                        st.error(f"生成出错: {chunk.error_message}")
                        st.session_state.is_streaming = False
                        break
            else:
                if comment['answer']:
                    answer_display, answer_needs_expand = truncate_text_for_display(comment['answer'], max_lines=5)
                    if answer_needs_expand:
                        with st.expander("查看完整回答", expanded=False):
                            st.markdown(comment['answer'])
                    else:
                        st.markdown(comment['answer'])
                else:
                    st.info("等待生成回答...")
            
            st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("---")


def render_footprint_section():
    with st.expander("🏃 学习足迹", expanded=False):
        if st.session_state.current_session_id:
            st.markdown("**本次学习路径**")
            footprints = get_footprints(st.session_state.current_session_id)
            if footprints:
                for fp in footprints[-10:]:
                    st.markdown(f"- {fp.action_type} @ {fp.created_at.strftime('%H:%M:%S')}")
            else:
                st.info("学习足迹将在问答过程中自动记录")
        else:
            st.markdown("暂无学习足迹")


def main():
    st.set_page_config(
        page_title="Maphiver - 流式知识河",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    
    init_db_sync()
    init_session_state()
    
    render_top_bar()
    
    st.markdown("---")
    
    left_col, center_col, right_col = st.columns([1, 3, 1])
    
    with left_col:
        with st.container():
            render_left_panel()
    
    with center_col:
        with st.container():
            render_center_panel()
    
    with right_col:
        with st.container():
            render_qa_comments()
    
    st.markdown("---")
    render_footprint_section()


if __name__ == "__main__":
    main()