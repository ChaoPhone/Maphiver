# 流式知识河 (Maphiver)

> **版本：0.1.0** | 2026-04-18

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
| PDF解析 | PyMuPDF (fitz) + python-docx |

## 项目结构

```
Maphiver/
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── views/          # 页面组件 (Read.vue)
│   │   ├── components/     # 子组件 (FootprintPanel, CardPanel)
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
│   ├── data/               # 数据存储目录
│   │   ├── maphiver.db     # SQLite 数据库
│   │   ├── uploads/        # 上传文件
│   │   └── images/         # 提取的图片
│   └── requirements.txt
│
├── docs/                   # 项目文档
│   ├── prd.md              # 产品需求文档
│   ├── api.md              # API 文档
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
| 历史恢复 | 归档会话可完整恢复 |
| 主题切换 | 支持浅色/深色主题 |
| 专注模式 | 隐藏侧边栏，沉浸式阅读 |

## 数据模型

5 张核心表：
- `documents` - 文档元数据
- `sessions` - 会话生命周期（draft/archived）
- `messages` - 问答记录
- `knowledge_cards` - 摘录批注
- `footprints` - 学习足迹

## API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/documents/upload` | POST | 上传文档 |
| `/api/documents/{id}/parse` | GET (SSE) | 流式解析文档 |
| `/api/qa/ask` | POST (SSE) | 流式问答 |
| `/api/sessions/` | POST/GET | 会话管理 |
| `/api/cards/` | POST/GET/PUT/DELETE | 知识卡片 CRUD |
| `/api/footprints/` | POST/GET | 学习足迹 |

## 版本历史

### v0.1.0 (2026-04-18)

**首次发布**

- ✅ 文档上传与解析（PDF/DOC/DOCX）
- ✅ AI 流式格式化输出
- ✅ 划词提问与流式回答
- ✅ 知识卡片摘录与批注
- ✅ 学习足迹记录
- ✅ 会话管理（draft/archived）
- ✅ 浅色/深色主题切换
- ✅ 专注模式
- ✅ LaTeX 公式渲染（含矩阵）
- ✅ 图片提取与展示

## 开发文档

详细文档位于 `docs/` 目录：
- `prd.md` - 产品需求文档
- `api.md` - API 接口文档
- `plans/` - 迭代计划与任务跟踪