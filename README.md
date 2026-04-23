# 流式知识河 (Maphiver)

> **版本：0.2.6** | 2026-04-24

一个以**对话流驱动、注重知识点自然关联与沉淀**的本地化AI学习伴侣。

## 项目简介

**目标用户**：理工科大学生（高等数学、线性代数、大学物理学习场景）

**核心痛点**：
- 阅读教材时存在概念理解障碍，读不懂、记不住
- 学后知识呈碎片化，无法有效关联新旧知识
- 传统AI对话难以把握整体知识结构
- 缺乏对"不懂"和"犯错"知识点的沉淀与回顾机制

**产品愿景**：让学习者在与AI的自由问答中，自然形成结构化的知识脉络，并专属保存在认知突破时刻的"知识财富"。

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + TypeScript + Element Plus + KaTeX + Vite |
| 后端 | FastAPI (Python) + SQLite |
| AI | DeepSeek API（流式输出） |
| 文件解析 | PyMuPDF (fitz) + python-docx |

## 项目结构

```
Maphiver/
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 页面组件 (Home.vue, Read.vue)
│   │   ├── components/     # 子组件
│   │   │   ├── DocumentUploader.vue
│   │   │   ├── FormulaRenderer.vue
│   │   │   ├── LeftSidebar.vue
│   │   │   ├── ParsingProgress.vue
│   │   │   ├── QAHistory.vue
│   │   │   ├── QAPanel.vue
│   │   │   └── FootprintPanel.vue
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── api/            # API 调用层
│   │   ├── utils/          # LaTeX 处理工具
│   │   ├── styles/         # 全局样式 (variables.css, markdown.css)
│   │   └── types/          # TypeScript 类型定义
│   └── package.json
│
├── backend/                # FastAPI 后端
│   ├── api/                # API 路由
│   │   ├── documents.py    # 文档上传/解析
│   │   ├── qa.py           # 问答 API
│   │   ├── sessions.py     # 会话管理
│   │   ├── cards.py        # 知识卡片
│   │   ├── footprints.py   # 学习足迹
│   │   ├── document_links.py  # 文档关联
│   │   ├── export.py       # 导出功能
│   │   └── images.py       # 图片服务
│   ├── services/           # 业务逻辑层
│   │   ├── ai_service.py   # DeepSeek 调用
│   │   ├── document_service.py
│   │   ├── qa_service.py
│   │   └── session_service.py
│   ├── models/             # Pydantic 数据模型
│   ├── repositories/       # SQLite 数据访问
│   ├── prompts/            # AI 提示词模板
│   ├── utils/              # 文档解析器
│   ├── config.py           # 配置文件
│   ├── data/               # 数据存储目录
│   │   ├── maphiver.db     # SQLite 数据库
│   │   ├── uploads/        # 上传文件
│   │   └── images/         # 提取的图片
│   ├── main.py
│   └── requirements.txt
│
├── docs/                   # 项目文档
│   ├── api-reference.md    # API 接口文档
│   ├── changelog/          # 变更记录
│   └── plans/              # 迭代计划
│
└── README.md
```

## 快速启动

### 1. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 配置环境变量

在 `backend/` 目录创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 3. 启动服务

```bash
# 后端 (端口 8000)
cd backend
python -m uvicorn main:app --reload --port 8000

# 前端 (端口 5173)
cd frontend
npm run dev
```

### 4. 访问应用

浏览器打开 http://localhost:5173

## 核心功能

| 功能 | 说明 |
|------|------|
| 文档上传解析 | 支持 PDF/DOC/DOCX，含公式文档自动格式化为 Markdown |
| AI 初始解答 | 上传后自动生成详细解答作为学习起点 |
| 流式问答 | 选中文本进行上下文感知问答，逐字渲染 |
| 知识卡片 | 一键摘录 AI 回答，添加批注保存 |
| 学习足迹 | 自动记录提问轨迹，生成探索路径 |
| 会话管理 | 支持置顶、收藏、批量操作，重命名 |
| 历史恢复 | 归档会话可完整恢复，文档内容缓存避免重复解析 |
| 主题切换 | 支持浅色/深色主题 |
| 专注模式 | 隐藏侧边栏，沉浸式阅读 |
| LaTeX 公式 | 支持行内公式和块级公式渲染（含矩阵） |
| 文档关联 | 跨文档知识关联与引用 |

## 数据模型

5 张核心表：

| 表名 | 描述 |
|------|------|
| `documents` | 文档元数据（包含解析后的 Markdown 内容） |
| `sessions` | 会话生命周期（draft/archived，支持置顶/收藏） |
| `messages` | 问答记录（含选中文本上下文） |
| `knowledge_cards` | 摘录批注 |
| `footprints` | 学习足迹 |

## API 端点

完整 API 文档请参阅 `docs/api-reference.md`

| 模块 | 端点数 | 主要功能 |
|------|--------|----------|
| 健康检查 | 1 | 服务状态 |
| 文档管理 | 6 | 上传/查询/解析/删除/内容获取 |
| 会话管理 | 7 | CRUD/置顶/收藏/归档 |
| 问答系统 | 3 | 提问/历史/快捷问题 |
| 知识卡片 | 5 | CRUD |
| 足迹记录 | 2 | 创建/查询 |
| 文档关联 | 4 | 创建/查询/删除 |
| 导出功能 | 1 | 导出会话内容 |
| 图片资源 | 1 | 获取图片文件 |

## 版本历史

### v0.2.6 (2026-04-24)

**Bug 修复**：
- 修复 QA 提问后 LaTeX 公式渲染失效的问题（QA 不再覆盖已格式化的文档内容）
- 优化流式输出内部拼接性能（list append 替代字符串拼接）

### v0.2.5 (2026-04-22)

**阅读体验优化**：
- 衬线字体应用（整个阅读页使用 Georgia/Noto Serif SC）
- 标题栏简化（只显示可编辑的会话名）
- 文档字体调大（正文 18px，行高 2）
- QA 卡片水平固定（右侧 20px，竖直动态跟随）
- QA 问答自动代入上下文（前后 block 内容）

**QA 卡片创意设计**：
- 引用格式（选中文本斜体 + 左边框强调）
- 折页关闭（右上角三角折页，hover 卷起变色显示 X）
- 错位阴影（两层深色卡片，与主卡片同步动态）
- 下划线滑动按钮（hover 时下划线从右滑入）
- 渐入渐出动画（从右侧滑入 + 缩放）
- 摘录按钮展开（hover 时文字向左展开）

**渲染修复**：
- FormulaRenderer 样式优化（不再覆盖全局 markdown.css）
- 公式保持数学字体（不受衬线字体影响）

### v0.2.0 (2026-04-22)

**新增功能**：
- 会话置顶功能（重要会话优先显示）
- 会话收藏功能（星标标记）
- 会话批量选中与删除
- 会话重命名
- 文档解析内容缓存（避免重复解析）
- 问答上下文存储（selected_text 保存）
- 首页布局优化（滚动区域、紧凑设计）
- QA 面板智能定位（跟随选中文本）

### v0.1.0 (2026-04-18)

**首次发布**：
- 文档上传与解析（PDF/DOC/DOCX）
- AI 流式格式化输出
- 划词提问与流式回答
- 知识卡片摘录与批注
- 学习足迹记录
- 会话管理（draft/archived）
- 浅色/深色主题切换
- 专注模式
- LaTeX 公式渲染（含矩阵）
- 图片提取与展示

## 开发文档

- `CONTRIBUTING.md` - 贡献规范（分支管理、Issue 规则）
- `docs/api-reference.md` - 完整 API 接口文档
- `docs/changelog/` - 迭代变更记录
- `docs/plans/` - 迭代计划与任务跟踪