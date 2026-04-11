import streamlit as st
import streamlit.components.v1 as components

from config import MAX_UPLOAD_SIZE_MB
from repositories.database import init_db_sync
from services import (
    upload_document,
    parse_document_stream,
    get_document,
    create_session,
    get_session,
    list_sessions,
    archive_session,
    stream_answer,
    get_quick_question,
    get_context_blocks,
    record_footprint,
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
    if "show_free_input" not in st.session_state:
        st.session_state.show_free_input = False
    if "active_quick_btn" not in st.session_state:
        st.session_state.active_quick_btn = None
    if "navigate_to_text" not in st.session_state:
        st.session_state.navigate_to_text = None


def handle_error(error: Exception):
    if isinstance(error, MaphiverError):
        st.error(f"❌ {error.message}")
    else:
        st.error("发生未知错误")
        st.exception(error)


def render_top_bar():
    st.markdown(
        """
        <style>
        .brand-header {
            font-size: 1.4em;
            font-weight: 600;
            color: #1E293B;
            padding: 10px 0 20px 0;
            letter-spacing: 0.5px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="brand-header">📙 Maphiver <span style="font-size:0.6em; color:#64748B; font-weight:400; margin-left:10px;">流式知识河</span></div>', unsafe_allow_html=True)


def render_left_panel():
    st.markdown("<div style='color:#64748B; font-size:0.9em; font-weight:600; margin-bottom:8px;'>会话状态</div>", unsafe_allow_html=True)
    
    if st.session_state.page_stage == "idle":
        st.markdown("<small style='color:#94A3B8;'>暂无进行中的阅读</small>", unsafe_allow_html=True)
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        st.markdown("<div style='color:#64748B; font-size:0.9em; font-weight:600; margin-bottom:8px;'>历史知识库</div>", unsafe_allow_html=True)
        archived_sessions = list_sessions()
        if archived_sessions:
            for session in archived_sessions[:5]:
                doc = get_document(session.document_id)
                if doc:
                    st.markdown(f"""
                    <div style="background:#F8FAFC; padding:8px; border-radius:6px; margin-bottom:6px; border:1px solid #E2E8F0; font-size:0.85em; color:#334155;">
                        📦 {doc.filename}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("<small style='color:#94A3B8;'>无历史</small>", unsafe_allow_html=True)
    
    elif st.session_state.page_stage in ["parsing", "ready"]:
        if st.session_state.current_document_id:
            doc = get_document(st.session_state.current_document_id)
            if doc:
                pages_info = f"<br><span style='color:#94A3B8;'>共 {st.session_state.total_pages} 页</span>" if st.session_state.total_pages else ""
                st.markdown(f"""
                <div style="background:#EEF2FF; border-left:3px solid #6366F1; padding:10px; border-radius:0 6px 6px 0; font-size:0.85em; color:#312E81;">
                    <strong>📄 {doc.filename}</strong>{pages_info}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
        if st.session_state.current_session_id:
            session = get_session(st.session_state.current_session_id)
            if session:
                st.markdown(f"""
                <div style="font-size:0.85em; color:#475569; display:flex; align-items:center; gap:5px;">
                    <span>💡 当前问答数：</span>
                    <strong style="background:#F1F5F9; padding:2px 6px; border-radius:10px;">{len(st.session_state.qa_comments)}</strong>
                </div>
                """, unsafe_allow_html=True)
        
        if st.session_state.page_stage == "ready":
            st.markdown('<hr class="subtle-divider">', unsafe_allow_html=True)
            if st.button("🌊 汇入知识河 (结束阅读)", type="secondary", use_container_width=True, key="archive_btn"):
                try:
                    archive_session(st.session_state.current_session_id)
                    st.session_state.page_stage = "idle"
                    st.session_state.current_session_id = None
                    st.session_state.parsed_content = None
                    st.session_state.qa_comments = []
                    st.rerun()
                except Exception as e:
                    handle_error(e)


def render_center_panel():
    if st.session_state.page_stage == "idle":
        # 移除大白框，回归原生清爽样式
        st.markdown(f"<div style='text-align:center; padding:2rem 0; color:#64748B;'>上传 PDF 文档开始沉浸式阅读 (最大 {MAX_UPLOAD_SIZE_MB}MB)</div>", unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "",
            type=["pdf"],
            key="pdf_uploader",
            label_visibility="collapsed",
        )
        
        if uploaded_file is not None:
            _, col_btn, _ = st.columns([1, 2, 1])
            with col_btn:
                if st.button("开始解析文档 🚀", type="primary", use_container_width=True):
                    try:
                        with st.spinner("上传中..."):
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
        st.markdown("<h4 style='color:#334155; text-align:center; padding-top:2rem;'>文档解析中，请稍候...</h4>", unsafe_allow_html=True)
        progress_bar = st.progress(0)
        status_text = st.empty()
        content_preview = st.empty()
        
        try:
            progress_bar.progress(5)
            status_text.markdown("<div style='text-align:center; color:#64748B; font-size:0.9em; margin-top:10px;'>正在提取 PDF 文本结构...</div>", unsafe_allow_html=True)
            
            formatted_content = ""
            
            for chunk in parse_document_stream(st.session_state.current_document_id):
                if chunk.type == ChunkType.TEXT:
                    if chunk.metadata:
                        stage = chunk.metadata.get("stage", "")
                        if stage == "extracting":
                            progress_bar.progress(10)
                            status_text.markdown("<div style='text-align:center; color:#64748B;'>正在提取 PDF 文本结构...</div>", unsafe_allow_html=True)
                        elif stage == "extracted":
                            progress_bar.progress(30)
                            total_pages = chunk.metadata.get("total_pages", 0)
                            st.session_state.total_pages = total_pages
                            status_text.markdown(f"<div style='text-align:center; color:#64748B;'>AI 正在深度格式化 {total_pages} 页内容...</div>", unsafe_allow_html=True)
                        elif stage == "formatting":
                            progress_bar.progress(35)
                        elif stage == "streaming":
                            progress_bar.progress(50)
                            formatted_content += chunk.content or ""
                            content_preview.markdown(f"<div style='color:#94A3B8; font-size:0.85em; max-height:200px; overflow:hidden; opacity:0.5;'>{formatted_content}</div>", unsafe_allow_html=True)
                    else:
                        formatted_content += chunk.content or ""
                        content_preview.markdown(f"<div style='color:#94A3B8; font-size:0.85em; max-height:200px; overflow:hidden; opacity:0.5;'>{formatted_content}</div>", unsafe_allow_html=True)
                        
                elif chunk.type == ChunkType.DONE:
                    progress_bar.progress(90)
                    status_text.markdown("<div style='text-align:center; color:#64748B;'>正在构建语义索引...</div>", unsafe_allow_html=True)
                    
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
                    status_text.empty()
                    content_preview.empty()
                    
                    st.session_state.page_stage = "ready"
                    st.session_state.qa_comments = []
                    st.rerun()
                    
                elif chunk.type == ChunkType.ERROR:
                    progress_bar.progress(0)
                    status_text.markdown(f"<div style='text-align:center; color:#EF4444;'>❌ {chunk.error_message}</div>", unsafe_allow_html=True)
                    st.session_state.page_stage = "idle"
                    break
                    
        except Exception as e:
            progress_bar.progress(0)
            status_text.markdown("<div style='text-align:center; color:#EF4444;'>❌ 解析过程中断</div>", unsafe_allow_html=True)
            handle_error(e)
    
    elif st.session_state.page_stage == "ready":
        # 此时才渲染包含白底、边框和阴影的“纸张”容器
        st.markdown("""<div class="reading-area-card" style="background:white; border-radius:8px; padding:30px; box-shadow:0 1px 3px rgba(0,0,0,0.05); border:1px solid #E2E8F0; min-height:80vh;">""", unsafe_allow_html=True)
        if st.session_state.parsed_content:
            st.markdown(f'<div class="reading-area">{st.session_state.parsed_content}</div>', unsafe_allow_html=True)
        else:
            st.markdown("<div style='text-align:center; color:#94A3B8; padding-top:2rem;'>暂无内容</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # -----------------------------------------------------------------
        # 大胆实现：注入 JS 脚本，完成“历史记录点击 -> 滚动并高亮对应文本”的导航定位
        # -----------------------------------------------------------------
        nav_text = st.session_state.get('navigate_to_text')
        if nav_text:
            # 净化文本，防止打破 JS 字符串
            safe_text = nav_text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('\n', ' ')
            components.html(f"""
            <script>
                try {{
                    const parentDocs = window.parent.document;
                    // 查找阅读区内的所有可能包含文本的节点
                    const elements = parentDocs.querySelectorAll('.reading-area p, .reading-area li, .reading-area span, .reading-area td');
                    
                    // 取前40个字符作为锚点特征搜索，增加鲁棒性
                    const searchText = `{safe_text}`.trim().substring(0, 40); 
                    
                    for (let el of elements) {{
                        if (el.innerText && el.innerText.includes(searchText)) {{
                            // 平滑滚动到屏幕中央
                            el.scrollIntoView({{behavior: 'smooth', block: 'center'}});
                            
                            // 高亮闪烁效果
                            const originalBg = el.style.backgroundColor;
                            el.style.backgroundColor = '#FEF08A'; // 提示黄
                            el.style.borderRadius = '4px';
                            el.style.transition = 'background-color 0.6s ease-in-out';
                            
                            // 2.5秒后褪色
                            setTimeout(() => {{ 
                                el.style.backgroundColor = originalBg; 
                            }}, 2500);
                            
                            break;
                        }}
                    }}
                }} catch(e) {{
                    console.error("跨域或DOM检索限制:", e);
                }}
            </script>
            """, height=0)
            st.session_state.navigate_to_text = None


def handle_question(selected_text: str, question: str):
    if not selected_text.strip():
        st.warning("请先在上方粘贴或输入需要询问的文本")
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
    
    display_text = selected_text[:120] + "..." if len(selected_text) > 120 else selected_text
    
    # 新增：记录当前交互绑定的 block_id，为未来完全体的“侧边栏对齐批注”打基础
    comment = {
        "selected_text": display_text,
        "full_selected_text": selected_text,
        "question": question,
        "answer": "",
        "is_expanded": True,
        "is_streaming": True,
        "block_id": st.session_state.selected_block_id 
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


def render_right_panel():
    st.markdown(
        """
        <style>
        .assistant-title {
            color: #334155;
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .qa-source-block {
            border-left: 3px solid #CBD5E1;
            padding: 8px 12px;
            margin-bottom: 12px;
            background: #F8FAFC;
            border-radius: 0 6px 6px 0;
            font-size: 0.85em;
            color: #475569;
            font-style: italic;
        }
        .qa-question-badge {
            font-size: 0.8em;
            color: #0F172A;
            background: #E2E8F0;
            padding: 4px 10px;
            border-radius: 12px;
            display: inline-block;
            margin-bottom: 8px;
            font-weight: 500;
        }
        .qa-answer-block {
            color: #1E293B;
            font-size: 0.9em;
            line-height: 1.6;
            background: white;
            padding: 12px;
            border: 1px solid #E2E8F0;
            border-radius: 6px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.02);
        }
        .streaming-pulse {
            animation: pulse 1.5s infinite;
            border-left: 3px solid #3B82F6 !important;
            background: #EFF6FF !important;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    st.markdown('<div class="assistant-title">🤖 AI 学习助手</div>', unsafe_allow_html=True)
    
    if st.session_state.page_stage != "ready":
        st.markdown("<div style='color:#94A3B8; font-size:0.9em;'>文档就绪后，即可在此提问。</div>", unsafe_allow_html=True)
        return
    
    if st.session_state.is_streaming:
        render_streaming_qa()
        return
    
    # --- 输入与操作区 ---
    st.markdown("<div style='font-size:0.85em; color:#64748B; margin-bottom:4px;'>📌 目标文本 (粘贴或输入)</div>", unsafe_allow_html=True)
    
    input_text = st.text_area(
        "",
        value=st.session_state.selected_text,
        height=100,
        key="selected_text_input",
        placeholder="将左侧文档中不理解的段落粘贴至此...",
        label_visibility="collapsed",
    )
    
    if input_text != st.session_state.selected_text:
        st.session_state.selected_text = input_text
        st.session_state.show_free_input = False
        st.session_state.active_quick_btn = None
    
    if not st.session_state.selected_text.strip():
        render_history_qa()
        return
    
    # 快捷动作矩阵
    st.markdown("<div style='font-size:0.85em; color:#64748B; margin: 12px 0 6px 0;'>⚡ 快捷分析</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    col4, col5 = st.columns([1.5, 1.5])
    
    with col1:
        if st.button("解释详细", use_container_width=True, type="primary" if st.session_state.active_quick_btn == "详细" else "secondary"):
            st.session_state.active_quick_btn = "详细"
            st.session_state.show_free_input = False
            handle_question(st.session_state.selected_text, get_quick_question("详细"))
    with col2:
        if st.button("通俗简化", use_container_width=True, type="primary" if st.session_state.active_quick_btn == "简化" else "secondary"):
            st.session_state.active_quick_btn = "简化"
            st.session_state.show_free_input = False
            handle_question(st.session_state.selected_text, get_quick_question("简化"))
    with col3:
        if st.button("打个比方", use_container_width=True, type="primary" if st.session_state.active_quick_btn == "类比" else "secondary"):
            st.session_state.active_quick_btn = "类比"
            st.session_state.show_free_input = False
            handle_question(st.session_state.selected_text, get_quick_question("类比"))
    
    with col4:
        if st.button("给个例子", use_container_width=True, type="primary" if st.session_state.active_quick_btn == "举例" else "secondary"):
            st.session_state.active_quick_btn = "举例"
            st.session_state.show_free_input = False
            handle_question(st.session_state.selected_text, get_quick_question("举例"))
    with col5:
        if st.button("自定义提问", use_container_width=True, type="primary" if st.session_state.active_quick_btn == "自定义" else "secondary"):
            st.session_state.active_quick_btn = "自定义"
            st.session_state.show_free_input = True

    if st.session_state.show_free_input:
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        free_question = st.text_input(
            "",
            key="free_question_input",
            placeholder="输入具体问题，按回车发送...",
            label_visibility="collapsed",
        )
        if free_question.strip():
            handle_question(st.session_state.selected_text, free_question)
    
    st.markdown('<hr class="subtle-divider" style="margin:20px 0;">', unsafe_allow_html=True)
    
    # --- 历史区 ---
    render_history_qa()


def render_streaming_qa():
    if not st.session_state.qa_comments:
        return
    
    current_qa = st.session_state.qa_comments[-1]
    question_type = st.session_state.active_quick_btn or "自定义分析"
    
    st.markdown(f'<div class="qa-question-badge">🤔 {question_type}</div>', unsafe_allow_html=True)
    
    answer_placeholder = st.empty()
    full_answer = ""
    
    context_text = get_context_blocks(
        st.session_state.parsed_blocks,
        st.session_state.selected_block_id,
        current_qa['full_selected_text'],
    )
    if not context_text:
        context_text = current_qa['full_selected_text']
    
    for chunk in stream_answer(
        st.session_state.current_session_id,
        current_qa['question'],
        current_qa['full_selected_text'],
        context_text,
    ):
        if chunk.type == ChunkType.TEXT:
            full_answer += chunk.content or ""
            answer_placeholder.markdown(
                f'<div class="qa-answer-block streaming-pulse">{full_answer}</div>',
                unsafe_allow_html=True,
            )
        elif chunk.type == ChunkType.DONE:
            current_qa['answer'] = full_answer
            current_qa['is_streaming'] = False
            st.session_state.is_streaming = False
            record_footprint(
                st.session_state.current_session_id,
                "qa_complete",
                {"question": current_qa['question']},
            )
            st.rerun()
        elif chunk.type == ChunkType.ERROR:
            st.error(f"生成出错: {chunk.error_message}")
            st.session_state.is_streaming = False
            current_qa['is_streaming'] = False
            break


def render_history_qa():
    if not st.session_state.qa_comments:
        return
    
    st.markdown("<div style='font-size:0.85em; color:#64748B; margin-bottom:8px;'>📜 讨论记录</div>", unsafe_allow_html=True)
    
    # 倒序展示，最新的在上面
    for i, comment in reversed(list(enumerate(st.session_state.qa_comments))):
        if comment.get('is_streaming', False):
            continue
        
        # 优化标题显示：处理空问题、清理特殊字符截断
        raw_q = comment.get('question', '').strip()
        q_text = raw_q if raw_q else "对选中文本的分析"
        display_title = f"💬 {q_text[:16]}{'...' if len(q_text) > 16 else ''}"
        
        with st.expander(
            display_title,
            expanded=(i == len(st.session_state.qa_comments) - 1), 
        ):
            st.markdown(
                f'<div class="qa-source-block">"{comment["selected_text"]}"</div>',
                unsafe_allow_html=True,
            )
            
            if comment['answer']:
                st.markdown(f'<div class="qa-answer-block">{comment["answer"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown("<small style='color:#94A3B8;'>等待回答...</small>", unsafe_allow_html=True)
            
            st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
            
            # 引入按钮行：导航定位功能
            col1, col2 = st.columns(2)
            with col1:
                # 点击此按钮触发 JS 将中栏平滑滚动到此文本区域
                if st.button("📍 定位原文", key=f"nav_btn_{i}", use_container_width=True):
                    st.session_state.navigate_to_text = comment['full_selected_text']
                    st.rerun()
            with col2:
                if st.button("📝 摘录笔记", key=f"card_btn_{i}", use_container_width=True):
                    st.info("笔记功能开发中...")


def main():
    st.set_page_config(
        page_title="Maphiver - 流式知识河",
        page_icon="📙",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    
    # 全局排版及去噪 CSS
    st.markdown(
        """
        <style>
        /* 隐藏无用的 Streamlit 头部和菜单 */
        header { display: none !important; }
        #MainMenu { display: none !important; }
        footer { display: none !important; }
        
        /* 调整主容器间距 */
        .block-container { 
            padding-top: 2rem !important; 
            padding-bottom: 2rem !important;
            max-width: 95% !important;
        }
        
        /* 全局字体与分隔线优化 */
        * { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
        .subtle-divider { 
            border-top: 1px solid #E2E8F0; 
            margin: 16px 0; 
        }
        
        /* 阅读区沉浸式排版 */
        .reading-area {
            font-size: 1.05em;
            line-height: 1.8;
            color: #1E293B;
            padding: 0 1rem;
        }
        .reading-area p { margin-bottom: 1.2em; }
        
        /* 按钮细腻度调整 */
        div[data-testid="stButton"] button {
            border-radius: 6px;
            font-weight: 500;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    init_db_sync()
    init_session_state()
    
    render_top_bar()
    
    # 彻底去掉外层强制包裹的白底边框，让 center_panel 自行决定是否渲染
    left_col, center_col, right_col = st.columns([1.2, 5.5, 3])
    
    with left_col:
        render_left_panel()
    
    with center_col:
        render_center_panel()
    
    with right_col:
        render_right_panel()


if __name__ == "__main__":
    main()