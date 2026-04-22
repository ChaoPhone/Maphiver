# Changelog: 首页历史记录管理增强

**变更日期**: 2026-04-20
**决策者**: 已确认并实施

## 变更原因

首页需要更完善的历史记录管理功能，包括：
- 搜索历史记录
- 删除会话/文档
- 重命名会话（自定义名称）
- 显示原PDF名称 + 会话名称（默认为时间）

---

## 影响范围

| 模块 | 影响类型 | 说明 |
|------|----------|------|
| `backend/models/schemas.py` | 修改 | Session 添加 name 字段 |
| `backend/api/sessions.py` | 修改 | 添加 update/rename API |
| `backend/services/session_service.py` | 修改 | 添加 update_session 函数 |
| `frontend/src/types/index.ts` | 修改 | Session 添加 name 字段 |
| `frontend/src/api/index.ts` | 修改 | 添加 updateSession, deleteSession API |
| `frontend/src/views/Home.vue` | 修改 | 添加搜索、删除、重命名功能 |
| `frontend/src/stores/index.ts` | 修改 | 添加 updateSession, deleteSession 方法 |

---

## 新旧对比

### Session 数据结构

| 字段 | 旧版 | 新版 |
|------|------|------|
| id | ✓ | ✓ |
| document_id | ✓ | ✓ |
| name | ❌ | ✓（新增，默认为创建时间） |
| status | ✓ | ✓ |
| created_at | ✓ | ✓ |
| updated_at | ✓ | ✓ |
| document | ✓ | ✓ |

### Home.vue 功能

| 功能 | 旧版 | 新版 |
|------|------|------|
| 上传文档 | ✓ | ✓ |
| 文档列表 | ✓ | ✓ |
| 会话列表 | ✓ | ✓（增强） |
| 搜索 | ❌ | ✓（新增） |
| 删除会话 | ❌ | ✓（新增） |
| 删除文档 | ❌ | ✓（新增） |
| 重命名会话 | ❌ | ✓（新增） |
| 显示PDF+会话名 | ❌ | ✓（新增） |

---

## 实施步骤

### Phase 1: 后端修改

1. **修改 Session 模型**
   - `backend/models/schemas.py`: SessionResponse 添加 `name` 字段
   - `backend/repositories/database.py`: Session 实体添加 `name` 字段

2. **添加 update session API**
   - `backend/api/sessions.py`: 添加 `PUT /{session_id}` 接口
   - `backend/services/session_service.py`: 添加 `update_session` 函数

3. **添加 delete session API**
   - `backend/api/sessions.py`: 添加 `DELETE /{session_id}` 接口
   - `backend/services/session_service.py`: 添加 `delete_session` 函数

### Phase 2: 前端修改

1. **修改类型定义**
   - `frontend/src/types/index.ts`: Session 添加 `name?: string` 字段

2. **添加 API 方法**
   - `frontend/src/api/index.ts`: 添加 `updateSession`, `deleteSession`

3. **修改 Store**
   - `frontend/src/stores/index.ts`: 添加 `updateSession`, `deleteSession` 方法

4. **修改 Home.vue**
   - 添加搜索输入框
   - 添加删除按钮（会话/文档）
   - 添加重命名按钮（会话）
   - 显示格式：`{document.filename} - {session.name || session.created_at}`

---

## 验收标准

### V1: 搜索功能
- Given: 用户在首页
- When: 用户输入搜索关键词
- Then: 会话列表实时过滤显示匹配结果

### V2: 删除会话
- Given: 用户在首页会话列表
- When: 用户点击删除按钮并确认
- Then: 会话被删除，列表更新

### V3: 删除文档
- Given: 用户在首页文档列表
- When: 用户点击删除按钮并确认
- Then: 文档及其所有会话被删除，列表更新

### V4: 重命名会话
- Given: 用户在首页会话列表
- When: 用户点击重命名按钮，输入新名称并保存
- Then: 会话名称更新，列表显示新名称

### V5: 显示格式
- Given: 用户在首页会话列表
- When: 页面加载完成
- Then: 每条会话显示 `{PDF文件名} - {会话名称或时间}`