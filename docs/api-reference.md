# Maphiver API 文档

> **流式知识河** - FastAPI 后端 API 参考文档
>
> **Base URL**: `http://localhost:8000/api`
>
> **CORS 允许的源**:
> - `http://localhost:5173`
> - `http://localhost:5174`
> - `http://localhost:3000`

---

## 目录

- [健康检查](#1-健康检查-health)
- [文档管理](#2-文档管理-documents)
- [会话管理](#3-会话管理-sessions)
- [问答系统](#4-问答系统-qa)
- [足迹记录](#5-足迹记录-footprints)
- [知识卡片](#6-知识卡片-cards)
- [文档关联](#7-文档关联-document-links)
- [导出功能](#8-导出功能-export)
- [图片资源](#9-图片资源-images)

---

## 1. 健康检查 (Health)

### GET `/health`

服务健康状态检查。

**响应**

```json
{
  "status": "ok",
  "version": "C1",
  "timestamp": "2026-04-22T12:00:00.000000"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| status | string | 服务状态，`ok` 表示正常 |
| version | string | API 版本号 |
| timestamp | datetime | 服务器时间戳 |

---

## 2. 文档管理 (Documents)

**Base Path**: `/documents`

### POST `/documents/upload`

上传文档文件。

**请求**

- Content-Type: `multipart/form-data`
- Body: `file` (binary, 必填)

**支持的格式**: `.pdf`, `.doc`, `.docx`

**响应** `DocumentUploadResponse`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "论文.pdf",
  "status": "uploaded",
  "message": "文档上传成功"
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 400 | 文件名为空或不支持的文件格式 |
| 400 | 文件大小超过限制 |

---

### GET `/documents/`

获取所有文档列表。

**响应** `List[DocumentResponse]`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "filename": "论文.pdf",
    "file_path": "/path/to/file",
    "page_count": 10,
    "parsed_at": "2026-04-22T12:00:00.000000",
    "created_at": "2026-04-22T12:00:00.000000"
  }
]
```

| 字段 | 类型 | 描述 |
|------|------|------|
| id | string | 文档唯一标识符 (UUID) |
| filename | string | 文件名 |
| file_path | string | 服务器存储路径 |
| page_count | integer/null | 页数（解析后可用） |
| parsed_at | datetime/null | 解析时间 |
| created_at | datetime | 上传时间 |

---

### GET `/documents/{document_id}`

获取单个文档信息。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| document_id | string | 文档 ID (UUID) |

**响应** `DocumentResponse`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "论文.pdf",
  "file_path": "/path/to/file",
  "page_count": 10,
  "parsed_at": "2026-04-22T12:00:00.000000",
  "created_at": "2026-04-22T12:00:00.000000"
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 文档不存在 |

---

### GET `/documents/{document_id}/content`

获取文档解析后的内容（Markdown 格式）。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| document_id | string | 文档 ID (UUID) |

**响应** `DocumentContentResponse`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "论文.pdf",
  "raw_markdown": "# 标题\n\n这是文档内容...",
  "parsed_at": "2026-04-22T12:00:00.000000"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| raw_markdown | string/null | 解析后的 Markdown 内容 |

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 400 | 文档尚未解析 |
| 404 | 文档不存在 |

---

### GET `/documents/{document_id}/parse`

### POST `/documents/{document_id}/parse`

解析文档（Server-Sent Events 流式响应）。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| document_id | string | 文档 ID (UUID) |

**响应类型**: `text/event-stream`

**SSE 事件流格式**:

```
data: {"type": "progress", "progress": 10, "stage": "extracting"}

data: {"type": "text", "content": ""}

data: {"type": "progress", "progress": 30, "stage": "extracted", "total_pages": 10, "block_count": 50}

data: {"type": "progress", "progress": 50, "stage": "formatting"}

data: {"type": "done", "total_pages": 10, "blocks": [...], "raw_markdown": "..."}

data: {"type": "error", "error": "错误信息"}
```

| 进度阶段 | progress 值 | 描述 |
|----------|-------------|------|
| extracting | 10 | 正在提取文本 |
| extracted | 30 | 文本提取完成 |
| formatting | 50 | 正在格式化 |
| streaming | 70 | 流式输出中 |
| done | 100 | 完成 |

---

### DELETE `/documents/{document_id}`

删除文档及其所有关联数据。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| document_id | string | 文档 ID (UUID) |

**响应**

```json
{
  "status": "deleted",
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 文档不存在 |

---

## 3. 会话管理 (Sessions)

**Base Path**: `/sessions`

### POST `/sessions/`

创建新的阅读会话。

**请求** `SessionCreateRequest`

```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| document_id | string | 是 | 关联的文档 ID |

**响应** `SessionResponse`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": null,
  "status": "draft",
  "is_pinned": false,
  "is_starred": false,
  "created_at": "2026-04-22T12:00:00.000000",
  "updated_at": "2026-04-22T12:00:00.000000"
}
```

| 字段 | 类型 | 描述 |
|------|------|------|
| status | string | `draft` (草稿) / `archived` (已归档) |
| is_pinned | boolean | 是否置顶 |
| is_starred | boolean | 是否收藏 |

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 文档不存在 |

---

### GET `/sessions/`

获取所有会话列表。

**查询参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| status | string | 按状态过滤 (`draft` / `archived`) |

**响应** `SessionListResponse`

```json
{
  "sessions": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "第一章笔记",
      "status": "draft",
      "is_pinned": true,
      "is_starred": false,
      "created_at": "2026-04-22T12:00:00.000000",
      "updated_at": "2026-04-22T12:00:00.000000",
      "document": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "filename": "论文.pdf",
        "file_path": "/path/to/file",
        "page_count": 10,
        "created_at": "2026-04-22T12:00:00.000000"
      }
    }
  ],
  "total": 1
}
```

**排序规则**: 按 `is_pinned DESC, updated_at DESC`（置顶优先，按更新时间倒序）

---

### GET `/sessions/{session_id}`

获取单个会话详情。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| session_id | string | 会话 ID (UUID) |

**响应** `SessionResponse` (包含嵌套的 document 对象)

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 会话不存在 |

---

### PUT `/sessions/{session_id}`

更新会话名称。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| session_id | string | 会话 ID (UUID) |

**请求** `SessionUpdateRequest`

```json
{
  "name": "新名称"
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| name | string | 否 | 新名称 |

**响应** `SessionResponse`

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 会话不存在 |

---

### PUT `/sessions/{session_id}/pin-star`

更新会话的置顶/收藏状态。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| session_id | string | 会话 ID (UUID) |

**请求** `SessionPinStarRequest`

```json
{
  "is_pinned": true,
  "is_starred": false
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| is_pinned | boolean | 否 | 是否置顶 |
| is_starred | boolean | 否 | 是否收藏 |

> 至少需要提供一个字段

**响应** `SessionResponse`

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 会话不存在 |

---

### DELETE `/sessions/{session_id}`

删除会话及其所有关联数据（问答历史、知识卡片、足迹）。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| session_id | string | 会话 ID (UUID) |

**响应**

```json
{
  "status": "deleted",
  "session_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 会话不存在 |

---

### PUT `/sessions/{session_id}/archive`

归档会话。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| session_id | string | 会话 ID (UUID) |

**响应** `SessionResponse` (status 变为 `archived`)

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 400 | 会话已归档 |
| 404 | 会话不存在 |

---

## 4. 问答系统 (QA)

**Base Path**: `/qa`

### POST `/qa/ask`

向 AI 提问（Server-Sent Events 流式响应）。

**请求** `AskRequest`

```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "question": "这段内容的主要观点是什么？",
  "selected_text": "选中的文本内容...",
  "block_id": "block_123"
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| session_id | string | 是 | 会话 ID |
| question | string | 是 | 问题内容 |
| selected_text | string | 否 | 选中的文本 |
| block_id | string | 否 | 关联的文本块 ID |

**响应类型**: `text/event-stream`

**SSE 事件流格式**:

```
data: {"type": "text", "content": "这是 AI 的回答..."}

data: {"type": "done"}

data: {"type": "error", "error": "错误信息"}
```

---

### GET `/qa/history/{session_id}`

获取会话的问答历史。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| session_id | string | 会话 ID (UUID) |

**响应** `QAHistoryResponse`

```json
{
  "messages": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "session_id": "660e8400-e29b-41d4-a716-446655440001",
      "question": "这段内容的主要观点是什么？",
      "selected_text": "选中的文本内容...",
      "answer": "AI 的回答内容...",
      "block_id": "block_123",
      "created_at": "2026-04-22T12:00:00.000000"
    }
  ]
}
```

---

### GET `/qa/quick-questions`

获取快捷问题模板。

**响应** `QuickQuestionsResponse`

```json
{
  "questions": [
    {"type": "详细", "template": "请详细解释这段内容"},
    {"type": "简化", "template": "请用通俗的语言简化这段内容"},
    {"type": "类比", "template": "请用一个类比来解释这段内容"},
    {"type": "解题", "template": "请给出这道题的详细解答步骤"}
  ]
}
```

---

## 5. 足迹记录 (Footprints)

**Base Path**: `/footprints`

### POST `/footprints/`

创建足迹记录。

**请求** `FootprintCreateRequest`

```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "action_type": "scroll",
  "context": {"page": 1, "position": 100},
  "message_id": "770e8400-e29b-41d4-a716-446655440002"
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| session_id | string | 是 | 会话 ID |
| action_type | string | 是 | 动作类型 |
| context | object | 否 | 上下文数据 |
| message_id | string | 否 | 关联的消息 ID |

**响应** `FootprintResponse`

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "message_id": "770e8400-e29b-41d4-a716-446655440002",
  "action_type": "scroll",
  "context": {"page": 1, "position": 100},
  "created_at": "2026-04-22T12:00:00.000000"
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 会话不存在 |

---

### GET `/footprints/{session_id}`

获取会话的所有足迹记录。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| session_id | string | 会话 ID (UUID) |

**响应** `FootprintListResponse`

```json
{
  "footprints": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "session_id": "660e8400-e29b-41d4-a716-446655440001",
      "message_id": "770e8400-e29b-41d4-a716-446655440002",
      "action_type": "scroll",
      "context": {"page": 1, "position": 100},
      "created_at": "2026-04-22T12:00:00.000000"
    }
  ],
  "total": 1
}
```

---

## 6. 知识卡片 (Cards)

**Base Path**: `/cards`

### POST `/cards/`

创建知识卡片。

**请求** `CardCreateRequest`

```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "source_text": "这是从文档中摘录的重要内容...",
  "annotation": "我的批注",
  "block_id": "block_123"
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| session_id | string | 是 | 会话 ID |
| source_text | string | 是 | 摘录的原文 |
| annotation | string | 否 | 批注 |
| block_id | string | 否 | 关联的文本块 ID |

**响应** `CardResponse`

```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "source_text": "这是从文档中摘录的重要内容...",
  "annotation": "我的批注",
  "block_id": "block_123",
  "created_at": "2026-04-22T12:00:00.000000"
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 会话不存在 |

---

### GET `/cards/`

获取知识卡片列表。

**查询参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| session_id | string | 按会话 ID 过滤（可选） |

**响应** `CardListResponse`

```json
{
  "cards": [
    {
      "id": "990e8400-e29b-41d4-a716-446655440004",
      "session_id": "660e8400-e29b-41d4-a716-446655440001",
      "source_text": "这是从文档中摘录的重要内容...",
      "annotation": "我的批注",
      "block_id": "block_123",
      "created_at": "2026-04-22T12:00:00.000000"
    }
  ],
  "total": 1
}
```

---

### GET `/cards/{card_id}`

获取单个知识卡片。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| card_id | string | 卡片 ID (UUID) |

**响应** `CardResponse`

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 卡片不存在 |

---

### PUT `/cards/{card_id}`

更新知识卡片的批注。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| card_id | string | 卡片 ID (UUID) |

**请求** `CardUpdateRequest`

```json
{
  "annotation": "更新后的批注内容"
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| annotation | string | 是 | 新的批注内容 |

**响应** `CardResponse`

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 卡片不存在 |

---

### DELETE `/cards/{card_id}`

删除知识卡片。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| card_id | string | 卡片 ID (UUID) |

**响应**

```json
{
  "status": "deleted",
  "card_id": "990e8400-e29b-41d4-a716-446655440004"
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 卡片不存在 |

---

## 7. 文档关联 (Document Links)

**Base Path**: `/document-links`

### POST `/document-links/`

创建文档关联。

**请求** `DocumentLinkCreateRequest`

```json
{
  "source_document_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_document_id": "550e8400-e29b-41d4-a716-446655440001",
  "link_type": "reference",
  "context": "相关章节：第3章"
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| source_document_id | string | 是 | 源文档 ID |
| target_document_id | string | 是 | 目标文档 ID |
| link_type | string | 否 | 关联类型，默认 `reference` |
| context | string | 否 | 关联上下文 |

**响应** `DocumentLinkResponse`

```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440005",
  "source_document_id": "550e8400-e29b-41d4-a716-446655440000",
  "target_document_id": "550e8400-e29b-41d4-a716-446655440001",
  "link_type": "reference",
  "context": "相关章节：第3章",
  "target_document": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "filename": "另一篇论文.pdf",
    "file_path": "/path/to/file2",
    "page_count": 20,
    "created_at": "2026-04-22T12:00:00.000000"
  },
  "created_at": "2026-04-22T12:00:00.000000"
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 400 | 不能关联同一文档 |
| 400 | 文档关联已存在 |
| 404 | 源文档不存在 |
| 404 | 目标文档不存在 |

---

### GET `/document-links/source/{document_id}`

获取以指定文档为源的所有关联。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| document_id | string | 源文档 ID |

**响应** `DocumentLinkListResponse`

```json
{
  "links": [...],
  "total": 1
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 文档不存在 |

---

### GET `/document-links/target/{document_id}`

获取以指定文档为目标的所有关联。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| document_id | string | 目标文档 ID |

**响应** `DocumentLinkListResponse`

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 文档不存在 |

---

### DELETE `/document-links/{link_id}`

删除文档关联。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| link_id | string | 关联 ID |

**响应**

```json
{
  "message": "关联已删除"
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 关联不存在 |

---

## 8. 导出功能 (Export)

**Base Path**: `/export`

### POST `/export/`

导出会话内容（包含知识卡片和问答记录）。

**请求** `ExportRequest`

```json
{
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "format": "markdown",
  "include_cards": true,
  "include_qa": true
}
```

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| session_id | string | 是 | 会话 ID |
| format | string | 否 | 导出格式，默认 `markdown` |
| include_cards | boolean | 否 | 是否包含知识卡片，默认 `true` |
| include_qa | boolean | 否 | 是否包含问答记录，默认 `true` |

**响应** `ExportResponse`

```json
{
  "content": "# 论文\n\n---\n\n## 文档信息\n\n- 文件名: 论文.pdf\n- 页数: 10\n- 导出时间: 2026-04-22 12:00:00\n\n---\n\n## 知识卡片\n\n### 卡片 1\n\n**摘录内容：**\n这是从文档中摘录的重要内容...\n\n**批注：** 我的批注\n\n---\n\n## 问答记录\n\n### 问答 1\n\n**问题：** 这段内容的主要观点是什么？\n\n**回答：**\nAI 的回答内容...",
  "filename": "论文_export_20260422_120000.md",
  "format": "markdown"
}
```

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 会话不存在 |
| 404 | 文档不存在 |

---

## 9. 图片资源 (Images)

**Base Path**: `/images`

### GET `/images/{image_filename}`

获取图片文件。

**路径参数**

| 参数 | 类型 | 描述 |
|------|------|------|
| image_filename | string | 图片文件名 |

**响应**: 图片文件（自动识别 MIME 类型）

**支持的格式**: 所有常见图片格式（png, jpg, gif, webp 等）

**错误响应**

| 状态码 | 描述 |
|--------|------|
| 404 | 图片不存在 |

---

## 数据模型参考

### 枚举类型

#### SessionStatus
```python
class SessionStatus(str, Enum):
    DRAFT = "draft"
    ARCHIVED = "archived"
```

#### MessageRole
```python
class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
```

#### ChunkType
```python
class ChunkType(str, Enum):
    TEXT = "text"
    DONE = "done"
    ERROR = "error"
```

---

## 错误响应格式

所有 API 错误均遵循以下格式：

```json
{
  "detail": "错误描述信息"
}
```

| HTTP 状态码 | 含义 |
|-------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 版本历史

| 版本 | 日期 | 描述 |
|------|------|------|
| C1 | 2026-04-22 | 初始版本 |
| C2 | 2026-04-22 | 添加会话置顶/收藏功能、文档解析内容存储 |
