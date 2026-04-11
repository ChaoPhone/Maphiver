# MVP主页面实施任务拆解（Streamlit架构版）

关联基线文档：[根据需求，细化MVP主页面实现.md](./根据需求，细化MVP主页面实现.md)

## 1. 架构结论

本拆解按 **Streamlit 单体应用** 执行：

| 层级 | 技术选型 | 职责 |
|------|----------|------|
| **整体框架** | Streamlit | 页面路由、状态管理（st.session_state）、左右侧边栏渲染 |
| **高阶交互区** | HTML/JS 自定义组件 | 中栏 PDF Markdown 渲染、鼠标划词监听、迷你菜单弹出、window.parent.postMessage 通信 |
| **后端逻辑** | 纯 Python | SQLite 数据库操作、Generator 函数对接 DeepSeek API 实现流式输出 |

核心原则：

1. **不需要 RESTful API**：前端交互直接绑定 Python 函数，状态全部走 `st.session_state`。
2. **组件化 Python 应用**：将传统"前后端分离设计思维"转化为"模块化 Python 应用设计思维"。
3. **解耦但不过度解耦**：优先可读可改，单文件可接受，但必须按职责分段。

---

## 2. 目录与落点

建议仓库结构：

```
maphiver/
├── app.py                      # Streamlit 应用入口
├── components/
│   └── reading_panel/          # 中栏自定义组件（HTML/JS）
│       ├── frontend/
│       │   ├── src/
│       │   │   └── index.tsx   # React 组件（划词、渲染、通信）
│       │   └── package.json
│             └── vite.config.ts
│       └── __init__.py         # Streamlit 组件封装
├── services/
│   ├── __init__.py
│   ├── document_service.py     # 文档上传、解析、存储
│   ├── session_service.py      # 会话生命周期管理
│   ├── qa_service.py           # 问答编排、Prompt 模板
│   ├── card_service.py         # 知识卡片 CRUD
│   └── ai_service.py           # DeepSeek API 调用、流式生成器
├── repositories/
│   ├── __init__.py
│   └── database.py             # SQLite 连接、ORM 映射、CRUD 原子操作
├── models/
│   ├── __init__.py
│   └── schemas.py              # Pydantic 数据模型、类型定义
├── utils/
│   ├── __init__.py
│   └── exceptions.py           # 自定义异常类
├── config.py                   # 配置管理（API Key、路径等）
├── requirements.txt
└── data/
    └── maphiver.db             # SQLite 数据库文件
```

---

## 3. 数据库模型设计（A0 必须冻结）

### 3.1 ER 图

```
┌─────────────────┐       ┌─────────────────┐
│    documents    │       │    sessions     │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │───┐   │ id (PK)         │
│ filename        │   │   │ document_id(FK) │───┐
│ file_path       │   └──►│ status          │   │
│ page_count      │       │ created_at      │   │
│ parsed_at       │       │ updated_at      │   │
│ created_at      │       └─────────────────┘   │
└─────────────────┘                             │
                                                │
┌─────────────────┐       ┌─────────────────┐   │
│    messages     │       │  knowledge_cards│   │
├─────────────────┤       ├─────────────────┤   │
│ id (PK)         │       │ id (PK)         │   │
│ session_id (FK) │◄──────│ session_id (FK) │◄──┘
│ role            │       │ source_text     │
│ content         │       │ annotation      │
│ block_id        │       │ block_id        │
│ created_at      │       │ created_at      │
└─────────────────┘       └─────────────────┘
        │
        ▼
┌─────────────────┐
│   footprints    │
├─────────────────┤
│ id (PK)         │
│ session_id (FK) │
│ message_id (FK) │
│ action_type     │
│ context         │
│ created_at      │
└─────────────────┘
```

### 3.2 建表 SQL

```sql
-- 文档表：存储上传的 PDF 元数据
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    page_count INTEGER,
    parsed_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 会话表：一次学习会话的生命周期
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'archived')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- 消息表：问答对话记录
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    block_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- 知识卡片表：摘录与批注
CREATE TABLE knowledge_cards (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    source_text TEXT NOT NULL,
    annotation TEXT,
    block_id TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- 学习足迹表：自动打点记录
CREATE TABLE footprints (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    message_id TEXT,
    action_type TEXT NOT NULL,
    context TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (message_id) REFERENCES messages(id)
);

-- 索引
CREATE INDEX idx_sessions_document ON sessions(document_id);
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_cards_session ON knowledge_cards(session_id);
CREATE INDEX idx_footprints_session ON footprints(session_id);
```

---

## 4. 内部函数接口设计（替代 API 契约）

### 4.1 文档服务 (document_service.py)

```python
from typing import Optional
from models.schemas import Document, ParseResult

def upload_document(file_bytes: bytes, filename: str) -> Document:
    """
    上传文档并保存到本地。
    
    Args:
        file_bytes: 文件二进制内容
        filename: 原始文件名
        
    Returns:
        Document: 文档元数据对象
        
    Raises:
        DocumentUploadError: 文件格式不支持或保存失败
    """
    pass

def parse_document(document_id: str) -> ParseResult:
    """
    解析文档，提取结构化内容。
    
    Args:
        document_id: 文档 ID
        
    Returns:
        ParseResult: 包含 blocks 列表的解析结果
        
    Raises:
        DocumentNotFoundError: 文档不存在
        ParseError: 解析失败
    """
    pass

def get_document(document_id: str) -> Optional[Document]:
    """获取文档元数据。"""
    pass

def delete_document(document_id: str) -> bool:
    """删除文档及其关联数据。"""
    pass
```

### 4.2 会话服务 (session_service.py)

```python
from typing import Optional, List
from models.schemas import Session, SessionStatus

def create_session(document_id: str) -> Session:
    """
    创建新会话。
    
    Args:
        document_id: 关联的文档 ID
        
    Returns:
        Session: 会话对象
    """
    pass

def get_session(session_id: str) -> Optional[Session]:
    """获取会话详情。"""
    pass

def update_session_status(session_id: str, status: SessionStatus) -> Session:
    """更新会话状态（draft -> archived）。"""
    pass

def list_sessions(status: Optional[SessionStatus] = None) -> List[Session]:
    """列出会话，支持按状态筛选。"""
    pass

def archive_session(session_id: str) -> Session:
    """归档会话（汇入知识河）。"""
    pass
```

### 4.3 问答服务 (qa_service.py)

```python
from typing import Generator, Optional
from models.schemas import Message, QuestionContext

def ask_question(
    session_id: str,
    question: str,
    context: Optional[QuestionContext] = None
) -> Message:
    """
    创建问题并返回用户消息记录。
    
    Args:
        session_id: 会话 ID
        question: 用户问题
        context: 选中文本上下文（可选）
        
    Returns:
        Message: 用户消息对象
    """
    pass

def stream_answer(
    session_id: str,
    message_id: str
) -> Generator[StreamChunk, None, None]:
    """
    流式生成 AI 回答。
    
    Yields:
        StreamChunk: 流式数据块
    """
    pass

def get_messages(session_id: str) -> List[Message]:
    """获取会话的所有消息。"""
    pass
```

### 4.4 知识卡片服务 (card_service.py)

```python
from typing import List, Optional
from models.schemas import KnowledgeCard

def create_card(
    session_id: str,
    source_text: str,
    annotation: Optional[str] = None,
    block_id: Optional[str] = None
) -> KnowledgeCard:
    """创建知识卡片。"""
    pass

def get_card(card_id: str) -> Optional[KnowledgeCard]:
    """获取单张卡片。"""
    pass

def list_cards(session_id: Optional[str] = None) -> List[KnowledgeCard]:
    """列出卡片，支持按会话筛选。"""
    pass

def update_card(card_id: str, annotation: str) -> KnowledgeCard:
    """更新卡片批注。"""
    pass

def delete_card(card_id: str) -> bool:
    """删除卡片。"""
    pass
```

### 4.5 足迹服务 (footprint_service.py)

```python
from typing import List
from models.schemas import Footprint

def record_footprint(
    session_id: str,
    action_type: str,
    context: Optional[dict] = None,
    message_id: Optional[str] = None
) -> Footprint:
    """记录学习足迹。"""
    pass

def get_footprints(session_id: str) -> List[Footprint]:
    """获取会话的所有足迹。"""
    pass
```

---

## 5. Python 生成器协议（替代 SSE）

### 5.1 流式数据块定义

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class ChunkType(Enum):
    TEXT = "text"           # 文本内容块
    DONE = "done"           # 流结束标记
    ERROR = "error"         # 错误标记

@dataclass
class StreamChunk:
    """流式输出数据块"""
    type: ChunkType
    content: Optional[str] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> dict:
        result = {"type": self.type.value}
        if self.content:
            result["content"] = self.content
        if self.error_message:
            result["error_message"] = self.error_message
        return result
```

### 5.2 生成器使用示例

```python
# ai_service.py 中的流式生成
def stream_answer(session_id: str, message_id: str) -> Generator[StreamChunk, None, None]:
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=build_messages(session_id),
            stream=True
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield StreamChunk(
                    type=ChunkType.TEXT,
                    content=chunk.choices[0].delta.content
                )
        
        yield StreamChunk(type=ChunkType.DONE)
        
    except Exception as e:
        yield StreamChunk(
            type=ChunkType.ERROR,
            error_message=str(e)
        )

# Streamlit 中消费生成器
def render_answer(session_id: str, message_id: str):
    answer_placeholder = st.empty()
    full_content = ""
    
    for chunk in stream_answer(session_id, message_id):
        if chunk.type == ChunkType.TEXT:
            full_content += chunk.content
            answer_placeholder.markdown(full_content)
        elif chunk.type == ChunkType.ERROR:
            st.error(f"生成出错: {chunk.error_message}")
            break
```

---

## 6. 异常处理体系（替代错误码）

### 6.1 异常类定义

```python
# utils/exceptions.py

class MaphiverError(Exception):
    """基础异常类"""
    def __init__(self, message: str, detail: Optional[dict] = None):
        self.message = message
        self.detail = detail or {}
        super().__init__(self.message)

# 文档相关异常
class DocumentError(MaphiverError):
    """文档操作基础异常"""
    pass

class DocumentNotFoundError(DocumentError):
    """文档不存在"""
    pass

class DocumentUploadError(DocumentError):
    """文档上传失败"""
    pass

class ParseError(DocumentError):
    """文档解析失败"""
    pass

# 会话相关异常
class SessionError(MaphiverError):
    """会话操作基础异常"""
    pass

class SessionNotFoundError(SessionError):
    """会话不存在"""
    pass

class SessionArchivedError(SessionError):
    """会话已归档，无法修改"""
    pass

# 问答相关异常
class QAError(MaphiverError):
    """问答操作基础异常"""
    pass

class AIServiceError(QAError):
    """AI 服务调用失败"""
    pass

# 卡片相关异常
class CardError(MaphiverError):
    """知识卡片操作基础异常"""
    pass

class CardNotFoundError(CardError):
    """卡片不存在"""
    pass
```

### 6.2 UI 反馈映射

```python
# 在 app.py 或各页面中统一处理

def handle_error(error: Exception):
    """统一错误处理，映射到 Streamlit UI 组件"""
    
    if isinstance(error, DocumentNotFoundError):
        st.error("📄 文档不存在，请重新上传")
    elif isinstance(error, DocumentUploadError):
        st.error(f"📤 上传失败: {error.message}")
    elif isinstance(error, ParseError):
        st.error(f"🔍 解析失败: {error.message}")
    elif isinstance(error, SessionNotFoundError):
        st.error("📁 会话不存在")
    elif isinstance(error, SessionArchivedError):
        st.warning("📦 会话已归档，如需修改请先恢复")
    elif isinstance(error, AIServiceError):
        st.error(f"🤖 AI 服务异常: {error.message}")
        st.toast("请检查 API Key 配置", icon="⚠️")
    elif isinstance(error, MaphiverError):
        st.error(f"❌ {error.message}")
    else:
        st.error("发生未知错误")
        st.exception(error)
```

---

## 7. 迭代计划

### A0：工程初始化与数据模型冻结

目标：Streamlit 应用可启动，数据库模型就绪。

任务：

1. 初始化项目目录结构。
2. 创建 `requirements.txt`，包含核心依赖：
   - `streamlit`
   - `pydantic`
   - `aiosqlite`（异步 SQLite）
   - `python-dotenv`
   - `openai`（DeepSeek API 兼容）
3. 实现 `models/schemas.py`：定义所有 Pydantic 数据模型。
4. 实现 `repositories/database.py`：数据库连接、建表、基础 CRUD。
5. 实现 `utils/exceptions.py`：异常类定义。
6. 创建 `config.py`：配置管理。
7. 创建最小可运行的 `app.py`：显示"Hello Maphiver"。

完成标准：

1. `streamlit run app.py` 可启动。
2. 数据库文件 `data/maphiver.db` 自动创建。
3. 所有表结构正确创建。
4. 健康检查：数据库连接正常。

---

### A1：页面骨架与状态管理

目标：三栏布局可渲染，状态流转正确。

前端任务：

1. 实现 `app.py` 三栏布局（左/中/右）。
2. 左栏：会话档案区（空状态占位）。
3. 中栏：上传区（初始化阶段）。
4. 右栏：默认折叠。
5. 实现 `st.session_state` 状态管理：
   - `current_session_id`
   - `page_stage`（idle / parsing / ready）
   - `selected_text`
   - `right_panel_open`

后端任务：

1. 实现 `session_service.py` 的 `create_session`、`get_session`。
2. 实现 `document_service.py` 的 `upload_document`、`get_document`。

完成标准：

1. 三栏布局正确显示。
2. 状态切换符合预期（idle -> parsing -> ready）。
3. 左栏可显示空状态提示。

---

### A2：上传解析与中栏阅读切换

目标：打通"上传 -> 解析 -> 阅读"主路径。

前端任务：

1. 中栏实现文件上传组件（`st.file_uploader`）。
2. 上传后触发解析，显示进度。
3. 解析完成后切换中栏为"面包屑 + 结构化正文"。
4. 左栏显示文档元信息。

后端任务：

1. 实现 `document_service.parse_document`：PDF 解析、结构化提取。
2. 返回结构化正文块：`block_id / page / chapter_path / content`。
3. 将解析结果存入数据库或本地文件。

完成标准：

1. 上传前中栏显示上传区。
2. 解析后上传区消失，中栏显示正文。
3. 左栏显示文档元数据。

---
## A2.5 规划：PyMuPDF + AI 预处理

### 流程设计

```
PDF 上传 → PyMuPDF 提取纯文本 → DeepSeek API 格式化 → 结构化 Markdown → 显示
```

### 任务拆解

| 任务ID | 内容 | 说明 |
|--------|------|------|
| A2.5-1 | 安装 PyMuPDF | `pip install pymupdf` |
| A2.5-2 | 实现 PDF 文本提取 | 使用 `fitz` 提取每页文本 |
| A2.5-3 | 实现 AI 预处理服务 | 调用 DeepSeek API 将纯文本转为 Markdown |
| A2.5-4 | 更新 document_service.py | 整合提取 + AI 格式化流程 |
| A2.5-5 | 更新 app.py | 显示格式化后的 Markdown |
| A2.5-6 | 验证完整流程 | 上传 PDF → 提取 → AI 格式化 → 显示 |

### AI 预处理 Prompt 设计

```
你是一个文档格式化助手。请将以下从 PDF 提取的纯文本转换为结构化的 Markdown 格式：

要求：
1. 识别标题层级（#, ##, ###）
2. 识别列表项（- 或 1. 2. 3.）
3. 识别数学公式，用 $...$ 或 $$...$$ 包裹
4. 识别表格，用 Markdown 表格格式
5. 保持段落结构清晰
6. 不要添加原文没有的内容

原始文本：
{extracted_text}

请输出格式化后的 Markdown：
```

### 技术细节

| 组件 | 实现 |
|------|------|
| **PDF 提取** | `fitz.open()` + `page.get_text()` |
| **AI 调用** | DeepSeek API（已有配置） |
| **流式输出** | Generator yield StreamChunk |
| **状态管理** | `st.session_state.parsed_content` |

### 预估时间

| 步骤 | 预估 |
|------|------|
| PyMuPDF 提取 | <1秒/页 |
| AI 格式化 | 3-5秒（取决于文本长度） |
| 总流程 | 约 10-15秒（10页 PDF） |

---

### A3：选中提问与流式回答

目标：打通核心学习价值链。

#### A3.1 技术方案

| 组件 | 实现方式 |
|------|---------|
| **文本选中** | Streamlit 原生 `st.text_area` + 手动输入选区（MVP 简化方案） |
| **右栏展开** | `st.session_state.right_panel_open` 状态控制 |
| **快捷提问** | 预设按钮：详细、简化、类比、举例 |
| **自由提问** | `st.text_input` + 发送按钮 |
| **流式回答** | DeepSeek API `stream=True` + Generator |
| **消息存储** | `messages` 表 + `st.session_state.messages` |
> 显示的形式有点像文档评论，用户选中文本后，点击提问按钮，模型会根据选中的文本回答问题，同时记录下用户的问题和回答。并且自动显示4-5行，自动折叠多余部分
#### A3.2 任务拆解

| 任务ID | 内容 | 文件 | 说明 |
|--------|------|------|------|
| A3-1 | 实现 qa_service.py | services/qa_service.py | ask_question + stream_answer 函数 |
| A3-2 | 扩展 ai_service.py | services/ai_service.py | 添加问答专用 Prompt 模板 |
| A3-3 | 实现 footprint_service.py | services/footprint_service.py | record_footprint 函数 |
| A3-4 | 更新 repositories/database.py | repositories/database.py | MessageRepository + FootprintRepository |
| A3-5 | 更新右栏 UI | app.py | 选区预览 + 快捷提问 + 流式渲染 |
| A3-6 | 验证完整流程 | - | 选中 → 提问 → 流式回答 → 入库 |

#### A3.3 Prompt 模板设计

```python
QA_SYSTEM_PROMPT = """你是一个专业的学习助手。用户正在阅读一篇文档，并选中了部分内容向你提问。
请基于选中的文本内容回答问题，回答应该：
1. 紧扣选中的文本，不要偏离主题
2. 如果涉及数学公式，使用 LaTeX 格式（$...$ 或 $$...$$）
3. 回答简洁清晰，适合学习场景"""

QA_USER_PROMPT = """选中的文本：
{selected_text}

问题：{question}"""
```
> 注意：选中文本内容喂给ai时，要注意不仅要喂给当前的文字，还要包含选中的该block及邻近2个block（总共3个block）的内容作为上下文输入。

#### A3.4 流式渲染策略

```python
def render_streaming_answer(session_id: str, question: str, selected_text: str):
    answer_placeholder = st.empty()
    full_content = ""
    
    for chunk in stream_answer(session_id, question, selected_text):
        if chunk.type == ChunkType.TEXT:
            full_content += chunk.content
            answer_placeholder.markdown(full_content)
        elif chunk.type == ChunkType.DONE:
            save_message(session_id, "assistant", full_content)
            record_footprint(session_id, "qa_complete")
        elif chunk.type == ChunkType.ERROR:
            st.error(f"生成出错: {chunk.error_message}")
            break
```

#### A3.5 完成标准

1. ✅ 右栏可展开/关闭
2. ✅ 选区预览正确显示
3. ✅ 快捷提问按钮可触发问答
4. ✅ 自由提问可发送
5. ✅ 流式回答实时渲染
6. ✅ 消息入库成功
7. ✅ 学习足迹记录成功

---

### A4：知识卡与归档恢复

目标：沉淀与回溯闭环。

#### A4.1 技术方案

| 组件 | 实现方式 |
|------|---------|
| **知识卡创建** | 回答区"摘录"按钮 + 批注输入框 |
| **卡片存储** | `knowledge_cards` 表 |
| **左栏展示** | 最近 5 张卡片预览 |
| **归档按钮** | 顶部栏"汇入知识河"按钮 |
| **历史恢复** | 点击历史会话 → 加载完整数据 |

#### A4.2 任务拆解

| 任务ID | 内容 | 文件 | 说明 |
|--------|------|------|------|
| A4-1 | 实现 card_service.py | services/card_service.py | create_card + list_cards + get_card |
| A4-2 | 更新 repositories/database.py | repositories/database.py | KnowledgeCardRepository |
| A4-3 | 更新右栏 UI | app.py | 回答区添加"摘录为知识卡"按钮 |
| A4-4 | 更新左栏 UI | app.py | 展示最近知识卡 + 历史会话列表 |
| A4-5 | 实现归档恢复 | app.py | 点击历史会话恢复完整数据 |
| A4-6 | 验证完整流程 | - | 回答 → 摘录 → 卡片 → 归档 → 恢复 |

#### A4.3 知识卡数据结构

```python
class KnowledgeCard(BaseModel):
    id: str
    session_id: str
    source_text: str          # 摘录的原文
    annotation: Optional[str]  # 用户批注
    block_id: Optional[str]    # 来源位置
    created_at: datetime
```

#### A4.4 归档恢复流程

```
点击历史会话
    ↓
加载 session 数据
    ↓
加载 document 数据
    ↓
加载 messages 数据
    ↓
加载 knowledge_cards 数据
    ↓
恢复到 st.session_state
    ↓
page_stage = "ready"
```

#### A4.5 完成标准

1. ✅ 回答区"摘录"按钮可点击
2. ✅ 批注弹层可输入并保存
3. ✅ 左栏展示最近知识卡
4. ✅ "汇入知识河"按钮可归档
5. ✅ 历史会话列表正确显示
6. ✅ 点击历史会话可完整恢复
7. ✅ 会话状态 draft → archived 可追踪

---

### A5：LaTeX 公式渲染闭环

目标：中栏正文与右栏回答都稳定渲染公式。

前端任务：

1. 集成 MathJax/KaTeX 渲染。
2. 中栏正文支持行内/块级公式。
3. 流式回答采用"段落完成后渲染"策略。

后端任务：

1. 标准化公式输出（`$...$` / `$$...$$`）。
2. 清洗非法标记，避免渲染报错。

完成标准：

1. 行内公式与块级公式正确显示。
2. 长公式不破版（可横向滚动）。
3. 流式场景不闪烁、不跳版。

---

## 8. 测试拆解

### F1：前端测试

1. 三栏显隐状态测试。
2. 文本选中与右栏展开测试。
3. 公式渲染视觉回归测试。

### B1：后端测试

1. 数据库 CRUD 测试。
2. 会话生命周期测试。
3. 流式问答生成器测试。

### E2E：端到端

1. 上传 -> 解析 -> 阅读
2. 选中 -> 提问 -> 流式回答
3. 摘录 -> 保存 -> 归档 -> 恢复

---

## 9. 风险与控制

1. 若 DeepSeek API 不稳定，增加重试机制和超时处理。
2. 若公式流式渲染抖动，采用"段落完成后渲染"策略。
3. 若自定义组件开发周期长，先用 `st.markdown` 替代，后续迭代优化。
4. 若模块过拆导致阅读困难，回收合并到 `services` 层。

---

## 10. 本周开工清单

1. 完成 A0（工程初始化 + 数据模型冻结）
2. 完成 A1（页面骨架 + 状态管理）
3. 完成 A2（上传解析与中栏显隐）
4. 完成 A3 最小链路（选中 -> 提问 -> 流式回答）
5. 完成 A5 首轮（中栏公式渲染）

完成以上 5 项后，即形成 Streamlit 架构的 MVP 可演示主链路。