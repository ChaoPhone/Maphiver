# TypeScript 版本转型方案 (分支 C)

> 基于 B3.3 版本，采用 **Vue 3 + TypeScript + FastAPI** 架构，渐进式迁移。

---

## 一、技术栈选型

| 层级 | 技术 | 理由 |
|------|------|------|
| **前端** | Vue 3 + TypeScript + Vite | 轻量、响应式、学习曲线平缓 |
| **UI组件** | Element Plus 或 Naive UI | 中文友好、组件丰富 |
| **状态管理** | Pinia | Vue 3 官方推荐，轻量 |
| **后端** | FastAPI | 自动 OpenAPI 文档、原生异步、流式响应支持 |
| **数据库** | SQLite (保持不变) | 轻量、无需额外部署 |
| **AI接口** | DeepSeek API (保持不变) | 已有集成经验 |

---

## 二、项目结构设计

```
Maphiver/
├── backend/                    # FastAPI 后端
│   ├── api/
│   │   ├── __init__.py
│   │   ├── documents.py        # 文档上传/解析 API
│   │   ├── sessions.py         # 会话管理 API
│   │   ├── qa.py               # 问答流式 API
│   │   └── footprints.py       # 学习足迹 API
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py          # Pydantic 模型 (复用现有)
│   │   └── database.py         # SQLAlchemy 模型
│   ├── services/               # 业务逻辑层 (复用现有)
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   ├── session_service.py
│   │   ├── ai_service.py
│   │   ├── qa_service.py
│   │   └── footprint_service.py
│   ├── repositories/           # 数据访问层 (复用现有)
│   ├── utils/
│   ├── config.py
│   ├── main.py                 # FastAPI 入口
│   └── requirements.txt
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── api/                # API 调用封装
│   │   │   ├── documents.ts
│   │   │   ├── sessions.ts
│   │   │   ├── qa.ts
│   │   │   └── streaming.ts    # SSE/WebSocket 流式处理
│   │   ├── components/
│   │   │   ├── DocumentUploader.vue
│   │   │   ├── ReadingPanel.vue
│   │   │   ├── BlockBreadcrumb.vue
│   │   │   ├── QAPanel.vue
│   │   │   ├── Sidebar.vue
│   │   │   └── StreamingAnswer.vue
│   │   ├── stores/             # Pinia 状态管理
│   │   │   ├── document.ts
│   │   │   ├── session.ts
│   │   │   ├── qa.ts
│   │   │   └── ui.ts
│   │   ├── views/
│   │   │   ├── HomeView.vue
│   │   │   ├── ReadingView.vue
│   │   │   └── ArchiveView.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── styles/
│   │   ├── App.vue
│   │   └── main.ts
│   ├── public/
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── data/                       # 数据目录 (保持不变)
│   ├── uploads/
│   └── maphiver.db
│
├── docs/                       # 文档
│   └── api.md                  # OpenAPI 文档
│
└── README.md
```

---

## 三、渐进式迁移计划

### C1: 后端骨架搭建 

**目标**: 创建 FastAPI 项目骨架，定义 API 接口契约

**步骤**:
1. 创建 `backend/` 目录结构
2. 编写 `main.py` 入口文件
3. 定义 Pydantic 请求/响应模型
4. 编写 API 路由骨架 (空实现，返回 mock 数据)
5. 配置 CORS 允许前端跨域

**冒烟测试**:
```bash
# 启动后端
cd backend && uvicorn main:app --reload --port 8000

# 测试 API 可访问
curl http://localhost:8000/api/health
# 期望: {"status": "ok", "version": "C1"}

# 测试 OpenAPI 文档生成
curl http://localhost:8000/docs
# 期望: Swagger UI 页面正常显示
```

**验收标准**:
- [ ] FastAPI 服务启动成功
- [ ] `/api/health` 返回健康检查
- [ ] `/docs` 显示 Swagger UI
- [ ] CORS 配置正确

---

### C2: 文档服务迁移 

**目标**: 迁移文档上传和解析功能

**API 设计**:
```
POST   /api/documents/upload      # 上传 PDF
GET    /api/documents/{id}        # 获取文档信息
DELETE /api/documents/{id}        # 删除文档
POST   /api/documents/{id}/parse  # 解析文档 (SSE 流式)
GET    /api/documents             # 文档列表
```

**步骤**:
1. 复用现有 `document_service.py`
2. 编写 `api/documents.py` 路由
3. 实现 SSE 流式解析响应
4. 测试文件上传和解析

**冒烟测试**:
```bash
# 上传测试文件
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@test.pdf"
# 期望: {"id": "...", "filename": "test.pdf", "status": "uploaded"}

# 解析文档 (SSE)
curl -N http://localhost:8000/api/documents/{id}/parse
# 期望: 流式返回解析进度和 blocks
```

**验收标准**:
- [ ] PDF 上传成功，返回 document_id
- [ ] SSE 流式解析正常工作
- [ ] 解析结果包含 blocks 数据
- [ ] 数据库记录正确创建

---

### C3: 会话服务迁移

**目标**: 迁移会话管理功能

**API 设计**:
```
POST   /api/sessions              # 创建会话
GET    /api/sessions/{id}         # 获取会话详情
PUT    /api/sessions/{id}/archive # 归档会话
GET    /api/sessions              # 会话列表 (支持筛选)
```

**步骤**:
1. 复用现有 `session_service.py`
2. 编写 `api/sessions.py` 路由
3. 测试会话 CRUD

**冒烟测试**:
```bash
# 创建会话
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"document_id": "..."}'
# 期望: {"id": "...", "document_id": "...", "status": "draft"}

# 归档会话
curl -X PUT http://localhost:8000/api/sessions/{id}/archive
# 期望: {"status": "archived"}
```

**验收标准**:
- [ ] 会话创建成功
- [ ] 会话状态更新正常
- [ ] 会话列表查询正常

---

### C4: 问答服务迁移 

**目标**: 迁移问答流式生成功能

**API 设计**:
```
POST   /api/qa/ask                # 提问 (SSE 流式回答)
GET    /api/qa/history/{session_id} # 获取问答历史
GET    /api/qa/quick-questions    # 获取快捷问题模板
```

**步骤**:
1. 复用现有 `qa_service.py` 和 `ai_service.py`
2. 编写 `api/qa.py` 路由
3. 实现 SSE 流式回答
4. 测试问答功能

**冒烟测试**:
```bash
# 提问 (SSE)
curl -N -X POST http://localhost:8000/api/qa/ask \
  -H "Content-Type: application/json" \
  -d '{"session_id": "...", "question": "解释这段内容", "selected_text": "...", "block_id": "..."}'
# 期望: 流式返回 AI 回答

# 获取历史
curl http://localhost:8000/api/qa/history/{session_id}
# 期望: 返回问答记录列表
```

**验收标准**:
- [ ] SSE 流式回答正常工作
- [ ] 问答历史记录正确
- [ ] block_id 关联正确

---

### C5: 前端骨架搭建

**目标**: 创建 Vue 3 项目骨架

**步骤**:
1. 使用 Vite 创建 Vue 3 + TS 项目
2. 安装 Element Plus / Naive UI
3. 配置 Pinia 状态管理
4. 配置 Vue Router
5. 编写 API 调用封装 (axios + SSE)

**冒烟测试**:
```bash
# 启动前端
cd frontend && npm run dev

# 访问 http://localhost:5173
# 期望: Vue 应用正常显示
# 期望: API 调用封装正常工作
```

**验收标准**:
- [ ] Vue 应用启动成功
- [ ] 路由配置正常
- [ ] Pinia store 正常工作
- [ ] API 调用能连接后端

---

### C6: 文档上传页面 

**目标**: 实现文档上传和解析进度展示

**组件**:
- `DocumentUploader.vue` - 文件上传组件
- `ParseProgress.vue` - 解析进度组件

**步骤**:
1. 实现文件上传 UI
2. 实现 SSE 进度监听
3. 解析完成后跳转到阅读页

**冒烟测试**:
```
# 手动测试流程:
1. 打开首页
2. 上传 PDF 文件
3. 观察解析进度条
4. 解析完成后自动跳转
# 期望: 整个流程顺畅无报错
```

**验收标准**:
- [ ] 文件上传 UI 正常
- [ ] SSE 进度实时更新
- [ ] 解析完成自动跳转

---

### C7: 阅读页面核心

**目标**: 实现逐块渲染和面包屑交互

**组件**:
- `ReadingPanel.vue` - 文档阅读区
- `BlockItem.vue` - 单个 block 渲染
- `BlockBreadcrumb.vue` - 面包屑按钮
- `QAPanel.vue` - 批注面板

**步骤**:
1. 实现 blocks 列表渲染
2. 实现面包屑按钮交互
3. 实现批注面板展开/收起
4. 实现快捷问题按钮

**冒烟测试**:
```
# 手动测试流程:
1. 进入阅读页面
2. 观察 blocks 逐块渲染
3. 点击面包屑按钮
4. 批注面板展开
5. 点击"详细"按钮提问
# 期望: AI 流式回答正常显示
```

**验收标准**:
- [ ] blocks 正确渲染
- [ ] 面包屑交互正常
- [ ] 批注面板展开正常
- [ ] 流式回答正常显示

---

### C8: 侧边栏和历史 

**目标**: 实现左侧栏和历史记录

**组件**:
- `Sidebar.vue` - 左侧栏
- `SessionCard.vue` - 会话卡片
- `HistoryList.vue` - 历史列表

**步骤**:
1. 实现会话状态展示
2. 实现历史会话列表
3. 实现归档功能

**冒烟测试**:
```
# 手动测试流程:
1. 观察左侧栏会话状态
2. 点击历史会话
3. 点击"归档"按钮
# 期望: 状态和历史正确显示
```

**验收标准**:
- [ ] 会话状态正确显示
- [ ] 历史列表正确加载
- [ ] 归档功能正常

---

### C9: 整体集成测试

**目标**: 全流程冒烟测试

**测试流程**:
```
1. 上传 PDF → 解析 → 进入阅读
2. 点击面包屑 → 提问 → 流式回答
3. 查看历史 → 定位原文
4. 归档会话 → 返回首页
5. 重新打开历史会话
```

**验收标准**:
- [ ] 全流程无报错
- [ ] 数据持久化正确
- [ ] UI 交互流畅

---

### C10: Streamlit 版本退役 

**目标**: 完成迁移，退役旧版本

**步骤**:
1. 对比新旧版本功能完整性
2. 删除 `app.py` (Streamlit 入口)
3. 更新 README 和部署文档
4. 保留 `components/` 目录作为参考

**验收标准**:
- [ ] 所有功能已迁移
- [ ] 旧代码已清理
- [ ] 文档已更新

---

## 四、API 接口契约详细设计

### 4.1 文档 API

```typescript
// POST /api/documents/upload
interface UploadResponse {
  id: string;
  filename: string;
  file_path: string;
  page_count: number | null;
  created_at: string;
}

// SSE /api/documents/{id}/parse
interface ParseChunk {
  type: 'progress' | 'block' | 'done' | 'error';
  data: {
    progress?: number;
    stage?: string;
    block?: ContentBlock;
    total_pages?: number;
    raw_markdown?: string;
    blocks?: ContentBlock[];
    error?: string;
  };
}

interface ContentBlock {
  id: string;
  type: string;
  page: number | null;
  chapter_path: string[];
  content: string;
}
```

### 4.2 会话 API

```typescript
// POST /api/sessions
interface CreateSessionRequest {
  document_id: string;
}

interface SessionResponse {
  id: string;
  document_id: string;
  status: 'draft' | 'archived';
  created_at: string;
  updated_at: string;
  document?: DocumentResponse;
}

// GET /api/sessions?status=draft|archived
interface SessionListResponse {
  sessions: SessionResponse[];
  total: number;
}
```

### 4.3 问答 API

```typescript
// POST /api/qa/ask (SSE)
interface AskRequest {
  session_id: string;
  question: string;
  selected_text: string;
  block_id: string | null;
  question_type?: string;
}

interface AnswerChunk {
  type: 'text' | 'done' | 'error';
  content?: string;
  error?: string;
}

// GET /api/qa/history/{session_id}
interface QAHistoryResponse {
  messages: {
    id: string;
    question: string;
    selected_text: string;
    answer: string;
    block_id: string | null;
    created_at: string;
  }[];
}

// GET /api/qa/quick-questions
interface QuickQuestionsResponse {
  questions: {
    type: string;
    template: string;
  }[];
}
```

---

## 五、前端状态管理设计

### 5.1 Document Store

```typescript
// stores/document.ts
interface DocumentState {
  currentDocument: DocumentResponse | null;
  parsedBlocks: ContentBlock[];
  parseProgress: number;
  parseStage: string;
  isParsing: boolean;
}
```

### 5.2 Session Store

```typescript
// stores/session.ts
interface SessionState {
  currentSession: SessionResponse | null;
  sessions: SessionResponse[];
  archivedSessions: SessionResponse[];
}
```

### 5.3 QA Store

```typescript
// stores/qa.ts
interface QAState {
  qaHistory: QAMessage[];
  currentAnswer: string;
  isStreaming: boolean;
  activeBlockId: string | null;
  activeQuickBtn: string | null;
}
```

### 5.4 UI Store

```typescript
// stores/ui.ts
interface UIState {
  pageStage: 'idle' | 'parsing' | 'ready';
  activeBlockId: string | null;
  showQAPanel: boolean;
  navigateToText: string | null;
}
```

---

## 六、关键技术点

### 6.1 SSE 流式响应

**后端 (FastAPI)**:
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse

async def parse_document_stream(document_id: str):
    async def generate():
        for chunk in parse_document(document_id):
            yield f"data: {json.dumps(chunk.to_dict())}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**前端 (Vue)**:
```typescript
async function listenParseProgress(documentId: string) {
  const eventSource = new EventSource(`/api/documents/${documentId}/parse`);
  
  eventSource.onmessage = (event) => {
    const chunk = JSON.parse(event.data);
    if (chunk.type === 'progress') {
      documentStore.setProgress(chunk.data.progress);
    } else if (chunk.type === 'block') {
      documentStore.addBlock(chunk.data.block);
    } else if (chunk.type === 'done') {
      eventSource.close();
      router.push('/reading');
    }
  };
}
```

### 6.2 面包屑交互

**组件设计**:
```vue
<template>
  <div class="block-row">
    <div class="block-text" v-html="block.content"></div>
    <button 
      class="breadcrumb"
      :class="{ active: isActive, has-comments: hasComments }"
      @click="togglePanel"
    >
      {{ hasComments ? `💬${commentCount}` : '··' }}
    </button>
  </div>
  <QAPanel v-if="isActive" :block="block" :comments="comments" />
</template>
```

---

## 七、风险与应对

| 风险 | 应对措施 |
|------|----------|
| SSE 在某些浏览器不兼容 | 提供 WebSocket fallback |
| 流式解析中断 | 增加断点续传机制 |
| 大文件解析慢 | 后端增加队列和进度缓存 |
| 前端状态复杂 | 使用 Pinia + TypeScript 强类型 |

---

## 八、后续扩展 (A4+)

完成 C10 后，可继续进行：

- **A4**: 知识卡片摘录功能
- **A5**: 学习足迹可视化
- **A6**: 多文档关联阅读
- **A7**: 导出功能 (PDF/Markdown)

---

## 九、时间估算

| 阶段 | 时间 | 依赖 |
|------|------|------|
| C1-C4 | 7天 | 无 |
| C5-C8 | 8天 | C1-C4 |
| C9-C10 | 2天 | C5-C8 |
| **总计** | **17天** | - |

---

## 十、启动命令

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

---

## 十一、已知问题与重构方案 (C阶段验收后补充)

### 11.1 LaTeX 公式渲染问题

**问题描述**:
- `pmatrix` 矩阵公式渲染报错：KaTeX 无法正确解析 `\begin{pmatrix}...\end{pmatrix}`
- 原因：AI 生成的 LaTeX 公式中换行符 `\\` 被 Markdown 解析器处理，导致公式结构破坏
- 现象：`$$\begin{pmatrix} a & b \\ c & d \end{pmatrix}$$` 渲染失败

**当前临时方案**:
- 前端 `Read.vue` 使用占位符保护机制：先保护 LaTeX → 处理 Markdown → 渲染 LaTeX
- 后端 `ai_service.py` prompt 要求矩阵使用行内格式 `$\begin{pmatrix}...\end{pmatrix}$`

**推荐重构方案**:
```typescript
// 方案A：预处理 LaTeX 换行符
function preprocessLatex(formula: string): string {
  // 将 LaTeX 换行符 \\ 替换为特殊标记，渲染时还原
  return formula.replace(/\\\\/g, '%%LATEX_NEWLINE%%')
}

// 方案B：使用 markdown-it + 自定义 LaTeX 插件
import MarkdownIt from 'markdown-it'
import { markdownItKatex } from '@mdit/plugin-katex'

const md = new MarkdownIt()
md.use(markdownItKatex, { throwOnError: false })
```

**优先级**: 高

---

### 11.2 前端组件缺失

**问题描述**:
对照计划文档，以下组件未实现：
- `ReadingPanel.vue` - 文档阅读区（当前直接在 Read.vue 中渲染）
- `BlockItem.vue` - 单个 block 渲染（未实现）
- `BlockBreadcrumb.vue` - 面包屑按钮（未实现）
- `QAPanel.vue` - 批注面板（当前直接在 Read.vue 中）
- `Sidebar.vue` - 左侧栏（未实现）
- `SessionCard.vue` - 会话卡片（未实现）
- `HistoryList.vue` - 历史列表（未实现）
- `ParseProgress.vue` - 解析进度组件（未实现）

**当前状态**:
- 功能已实现，但组件未拆分，代码集中在 `Read.vue` 和 `Home.vue`
- 不利于维护和复用

**推荐重构方案**:
1. 创建 `components/QAPanel.vue` - 抽离问答面板逻辑
2. 创建 `components/Sidebar.vue` - 抽离左侧栏逻辑
3. 创建 `components/ParseProgress.vue` - 抽离解析进度显示
4. `Read.vue` 改为组合这些组件

**优先级**: 中

---

### 11.3 API 调用方式不一致

**问题描述**:
- `parseDocument` 使用 `EventSource` (SSE)
- `askQuestionStream` 使用 `fetch` + `ReadableStream`
- 两种流式处理方式不一致，增加维护成本

**推荐重构方案**:
```typescript
// 统一使用 fetch + ReadableStream
export async function streamRequest(
  url: string,
  options: RequestInit,
  onChunk: (data: any) => void
): Promise<void> {
  const response = await fetch(url, options)
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    
    const text = decoder.decode(value)
    const lines = text.split('\n')
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        onChunk(JSON.parse(line.slice(6)))
      }
    }
  }
}
```

**优先级**: 低

---

### 11.4 状态管理优化

**问题描述**:
- 当前 `stores/index.ts` 将 document 和 session store 合在一个文件
- 缺少独立的 `qa.ts` 和 `ui.ts` store
- `qaMessages` 状态管理在 session store 中，不符合计划设计

**推荐重构方案**:
1. 拆分 `stores/document.ts`
2. 拆分 `stores/session.ts`
3. 创建 `stores/qa.ts` - 独立管理问答状态
4. 创建 `stores/ui.ts` - 管理 UI 状态（pageStage, activeBlockId, showQAPanel）

**优先级**: 中

---

### 11.5 后端 AI Prompt 改进

**问题描述**:
- 当前 prompt 对题目识别不够稳定
- LaTeX 公式格式规范需要更明确的示例
- 矩阵公式换行符处理问题

**推荐改进**:
```python
FORMAT_PROMPT = """
...
**【矩阵公式特殊处理】**：
- 矩阵元素之间用 `&` 分隔
- 矩阵行之间用 `\\\\` (双反斜杠)，但需确保 Markdown 不破坏
- 推荐格式：`$\begin{pmatrix} a & b \\\\ c & d \end{pmatrix}$`
- 或使用简化格式：`$\left[\begin{array}{cc} a & b \\ c & d \end{array}\right]$`
"""
```

**优先级**: 高

---

### 11.6 缺失功能

**问题描述**:
以下计划功能未实现：
- 知识卡片摘录功能 (A4)
- 学习足迹可视化 (A5)
- 归档功能 UI（后端 API 已实现，前端未接入）
- 快捷问题模板 API (`/api/qa/quick-questions`) - 后端已实现但前端未调用

**推荐方案**:
- C11: 实现归档功能 UI
- C12: 接入快捷问题模板 API
- 后续 A4-A5: 知识卡片和学习足迹

**优先级**: 中

---

## 十二、C阶段验收清单

| 阶段 | 状态 | 备注 |
|------|------|------|
| C1: 后端骨架 | ✅ 完成 | FastAPI + CORS + Health API |
| C2: 文档服务 | ✅ 完成 | 上传/解析 SSE 流式 |
| C3: 会话服务 | ✅ 完成 | CRUD + archive |
| C4: 问答服务 | ✅ 完成 | SSE 流式回答 |
| C5: 前端骨架 | ✅ 完成 | Vue 3 + Pinia + Router |
| C6: 文档上传页面 | ✅ 完成 | Upload.vue |
| C7: 阅读页面核心 | ⚠️ 部分完成 | LaTeX 渲染有问题 |
| C8: 侧边栏和历史 | ⚠️ 部分完成 | 组件未拆分 |
| C9: 整体集成测试 | ⚠️ 需验证 | LaTeX 问题影响体验 |
| C10: Streamlit退役 | ⏳ 待定 | 功能完整性确认后 |

---

**下一步**: 
1. 修复 LaTeX 矩阵公式渲染问题
2. 拆分前端组件
3. 完成集成测试
4. 确认功能完整性后退役 Streamlit 版本