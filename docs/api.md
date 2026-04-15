# Maphiver API 文档

## 基础信息

- **Base URL**: `/api`
- **协议**: HTTP + SSE (Server-Sent Events)
- **数据格式**: JSON

---

## 1. 健康检查

### GET /health

检查服务状态。

**响应**:
```json
{
  "status": "ok",
  "version": "C1",
  "timestamp": "2026-04-12T10:00:00"
}
```

---

## 2. 文档管理

### POST /documents/upload

上传 PDF 文档。

**请求**:
- Content-Type: `multipart/form-data`
- Body: `file` (PDF 文件)

**响应**:
```json
{
  "id": "uuid-string",
  "filename": "example.pdf",
  "status": "uploaded",
  "message": "文档上传成功"
}
```

**错误**:
- 400: 仅支持 PDF 文件
- 400: 文件大小超过限制 (50MB)

---

### GET /documents/

获取所有文档列表。

**响应**:
```json
[
  {
    "id": "uuid-string",
    "filename": "example.pdf",
    "file_path": "/data/uploads/uuid_example.pdf",
    "page_count": 10,
    "created_at": "2026-04-12T10:00:00"
  }
]
```

---

### GET /documents/{document_id}

获取单个文档详情。

**响应**:
```json
{
  "id": "uuid-string",
  "filename": "example.pdf",
  "file_path": "/data/uploads/uuid_example.pdf",
  "page_count": 10,
  "created_at": "2026-04-12T10:00:00"
}
```

**错误**:
- 404: 文档不存在

---

### DELETE /documents/{document_id}

删除文档。

**响应**:
```json
{
  "status": "deleted",
  "document_id": "uuid-string"
}
```

**错误**:
- 404: 文档不存在

---

### GET /documents/{document_id}/parse (SSE)

流式解析文档，返回 SSE 事件流。

**事件类型**:

1. **progress** - 解析进度
```json
{
  "type": "progress",
  "stage": "extracting|extracted|formatting|streaming",
  "progress": 10|30|50|70
}
```

2. **text** - 格式化文本流
```json
{
  "type": "text",
  "content": "markdown片段"
}
```

3. **done** - 解析完成
```json
{
  "type": "done",
  "total_pages": 10,
  "blocks": [
    {
      "id": "block-uuid",
      "content": "段落内容",
      "chapter_path": ["第一章", "1.1节"],
      "page": 1
    }
  ],
  "raw_markdown": "完整markdown文本"
}
```

4. **error** - 解析错误
```json
{
  "type": "error",
  "error": "错误信息"
}
```

---

## 3. 会话管理

### POST /sessions/

创建新会话。

**请求**:
```json
{
  "document_id": "uuid-string"
}
```

**响应**:
```json
{
  "id": "session-uuid",
  "document_id": "document-uuid",
  "status": "draft",
  "created_at": "2026-04-12T10:00:00",
  "updated_at": "2026-04-12T10:00:00"
}
```

**错误**:
- 404: 文档不存在

---

### GET /sessions/

获取会话列表。

**参数**:
- `status` (可选): `draft` | `archived`

**响应**:
```json
{
  "sessions": [
    {
      "id": "session-uuid",
      "document_id": "document-uuid",
      "status": "draft",
      "created_at": "2026-04-12T10:00:00",
      "updated_at": "2026-04-12T10:00:00"
    }
  ],
  "total": 5
}
```

---

### GET /sessions/{session_id}

获取会话详情（含关联文档信息）。

**响应**:
```json
{
  "id": "session-uuid",
  "document_id": "document-uuid",
  "status": "draft",
  "created_at": "2026-04-12T10:00:00",
  "updated_at": "2026-04-12T10:00:00",
  "document": {
    "id": "document-uuid",
    "filename": "example.pdf",
    "file_path": "/data/uploads/...",
    "page_count": 10,
    "created_at": "2026-04-12T10:00:00"
  }
}
```

**错误**:
- 404: 会话不存在

---

### PUT /sessions/{session_id}/archive

归档会话。

**响应**:
```json
{
  "id": "session-uuid",
  "document_id": "document-uuid",
  "status": "archived",
  "created_at": "...",
  "updated_at": "..."
}
```

**错误**:
- 404: 会话不存在
- 400: 会话已归档

---

## 4. QA问答

### POST /qa/ask (SSE)

流式问答，返回 SSE 事件流。

**请求**:
```json
{
  "session_id": "session-uuid",
  "question": "请解释这段内容",
  "selected_text": "选中的文本内容",
  "block_id": "block-uuid (可选)"
}
```

**事件类型**:

1. **text** - 回答文本流
```json
{
  "type": "text",
  "content": "回答片段"
}
```

2. **done** - 回答完成
```json
{
  "type": "done"
}
```

3. **error** - 回答错误
```json
{
  "type": "error",
  "error": "错误信息"
}
```

---

### GET /qa/history/{session_id}

获取问答历史记录。

**响应**:
```json
{
  "messages": [
    {
      "id": "message-uuid",
      "session_id": "session-uuid",
      "question": "请解释这段内容",
      "selected_text": "选中的文本",
      "answer": "AI的回答内容",
      "block_id": "block-uuid",
      "created_at": "2026-04-12T10:00:00"
    }
  ]
}
```

---

### GET /qa/quick-questions

获取快捷问题模板。

**响应**:
```json
{
  "questions": [
    { "type": "详细", "template": "请详细解释这段内容" },
    { "type": "简化", "template": "请用通俗的语言简化这段内容" },
    { "type": "类比", "template": "请用一个类比来解释这段内容" },
    { "type": "举例", "template": "请举一个具体的例子来说明这段内容" }
  ]
}
```

---

## 5. 学习足迹

### POST /footprints/

创建学习足迹记录。

**请求**:
```json
{
  "session_id": "session-uuid",
  "action_type": "ask|select|highlight",
  "context": { "额外上下文信息" },
  "message_id": "message-uuid (可选)"
}
```

**响应**:
```json
{
  "id": "footprint-uuid",
  "session_id": "session-uuid",
  "message_id": "message-uuid",
  "action_type": "ask",
  "context": {},
  "created_at": "2026-04-12T10:00:00"
}
```

**错误**:
- 404: 会话不存在

---

### GET /footprints/{session_id}

获取会话的学习足迹记录。

**响应**:
```json
{
  "footprints": [
    {
      "id": "footprint-uuid",
      "session_id": "session-uuid",
      "message_id": "message-uuid",
      "action_type": "ask",
      "context": {},
      "created_at": "2026-04-12T10:00:00"
    }
  ],
  "total": 5
}
```

---

## 6. 知识卡片

### POST /cards/

创建知识卡片。

**请求**:
```json
{
  "session_id": "session-uuid",
  "source_text": "摘录的原文",
  "annotation": "用户批注 (可选)",
  "block_id": "block-uuid (可选)"
}
```

**响应**:
```json
{
  "id": "card-uuid",
  "session_id": "session-uuid",
  "source_text": "摘录的原文",
  "annotation": "用户批注",
  "block_id": "block-uuid",
  "created_at": "2026-04-12T10:00:00"
}
```

**错误**:
- 404: 会话不存在

---

### GET /cards/

获取知识卡片列表。

**参数**:
- `session_id` (可选): 指定会话

**响应**:
```json
{
  "cards": [
    {
      "id": "card-uuid",
      "session_id": "session-uuid",
      "source_text": "摘录的原文",
      "annotation": "用户批注",
      "block_id": "block-uuid",
      "created_at": "2026-04-12T10:00:00"
    }
  ],
  "total": 5
}
```

---

### GET /cards/{card_id}

获取单个知识卡片详情。

**响应**:
```json
{
  "id": "card-uuid",
  "session_id": "session-uuid",
  "source_text": "摘录的原文",
  "annotation": "用户批注",
  "block_id": "block-uuid",
  "created_at": "2026-04-12T10:00:00"
}
```

**错误**:
- 404: 知识卡片不存在

---

### PUT /cards/{card_id}

更新卡片批注。

**请求**:
```json
{
  "annotation": "新的批注内容"
}
```

**响应**:
```json
{
  "id": "card-uuid",
  "session_id": "session-uuid",
  "source_text": "摘录的原文",
  "annotation": "新的批注内容",
  "block_id": "block-uuid",
  "created_at": "2026-04-12T10:00:00"
}
```

**错误**:
- 404: 知识卡片不存在

---

### DELETE /cards/{card_id}

删除知识卡片。

**响应**:
```json
{
  "status": "deleted",
  "card_id": "card-uuid"
}
```

**错误**:
- 404: 知识卡片不存在

---

## API 完整性检查

| 功能模块 | Streamlit版本 | FastAPI后端 | 前端调用 | 状态 |
|---------|--------------|-------------|---------|------|
| 文档上传 | ✅ | ✅ | ✅ | 完成 |
| 文档解析(SSE) | ✅ | ✅ | ✅ | 完成 |
| 文档列表 | ✅ | ✅ | ✅ | 完成 |
| 文档删除 | ✅ | ✅ | ✅ | 完成 |
| 会话创建 | ✅ | ✅ | ✅ | 完成 |
| 会话列表 | ✅ | ✅ | ✅ | 完成 |
| 会话详情 | ✅ | ✅ | ✅ | 完成 |
| 会话归档 | ✅ | ✅ | ✅ | 完成 |
| QA问答(SSE) | ✅ | ✅ | ✅ | 完成 |
| QA历史 | ✅ | ✅ | ✅ | 完成 |
| 快捷问题 | ✅ | ✅ | ✅ | 完成 |
| 学习足迹 | ✅ | ✅ | ✅ | 完成 |
| 知识卡片 | ✅ | ✅ | ✅ | 完成 |

---

## 前端调用检查

### 已实现的API调用 (frontend/src/api/index.ts)

| 函数 | API端点 | 状态 |
|-----|--------|------|
| `uploadDocument` | POST /documents/upload | ✅ |
| `getDocuments` | GET /documents/ | ✅ |
| `getDocument` | GET /documents/{id} | ✅ |
| `deleteDocument` | DELETE /documents/{id} | ✅ |
| `parseDocument` | GET /documents/{id}/parse (SSE) | ✅ |
| `createSession` | POST /sessions/ | ✅ |
| `getSession` | GET /sessions/{id} | ✅ |
| `archiveSession` | PUT /sessions/{id}/archive | ✅ |
| `getSessions` | GET /sessions/ | ✅ |
| `askQuestionStream` | POST /qa/ask (SSE) | ✅ |
| `getQAHistory` | GET /qa/history/{id} | ✅ |
| `getQuickQuestions` | GET /qa/quick-questions | ✅ |
| `healthCheck` | GET /health | ✅ |
| `getFootprints` | GET /footprints/{session_id} | ✅ |
| `createFootprint` | POST /footprints/ | ✅ |
| `getCards` | GET /cards/ | ✅ |
| `getCard` | GET /cards/{id} | ✅ |
| `createCard` | POST /cards/ | ✅ |
| `updateCard` | PUT /cards/{id} | ✅ |
| `deleteCard` | DELETE /cards/{id} | ✅ |

---

## 后端路由注册

所有API路由已在 `backend/main.py` 中注册：

```python
app.include_router(documents.router, prefix="/documents")
app.include_router(sessions.router, prefix="/sessions")
app.include_router(qa.router, prefix="/qa")
app.include_router(cards.router, prefix="/cards")
app.include_router(footprints.router, prefix="/footprints")
```