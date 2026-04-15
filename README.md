# 流式知识河 (Maphiver)

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
| 前端 | Vue 3 + TypeScript + Element Plus + KaTeX |
| 后端 | FastAPI (Python) |
| AI | DeepSeek API（流式输出） |
| 数据库 | SQLite（本地存储） |
| PDF解析 | PyMuPDF (fitz) |
| 构建 | Vite |

## 项目结构

```
Maphiver/
├── frontend/           # Vue 3 前端
│   ├── src/
│   │   ├── views/      # 页面组件
│   │   ├── stores/     # Pinia状态管理
│   │   ├── api/        # API调用层
│   │   ├── utils/      # 工具函数
│   │   └── styles/     # 全局样式
│   └── package.json
├── backend/            # FastAPI 后端
│   ├── api/            # API路由
│   ├── services/       # 业务逻辑层
│   ├── models/         # Pydantic数据模型
│   ├── database/       # SQLite数据访问
│   └── requirements.txt
├── docs/               # 项目文档
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
| PDF上传解析 | 支持含公式文档，自动格式化为Markdown |
| AI初始解答 | 上传后自动生成详细解答作为学习起点 |
| 流式问答 | 选中文本进行上下文感知问答，逐字渲染 |
| 知识卡片 | 一键摘录AI回答，添加批注保存 |
| 学习足迹 | 自动记录提问轨迹，生成探索路径 |
| 历史恢复 | 归档会话可完整恢复 |

## 数据模型

5张核心表：
- `documents` - 文档元数据
- `sessions` - 会话生命周期（draft/archived）
- `messages` - 问答记录
- `knowledge_cards` - 摘录批注
- `footprints` - 学习足迹

## 开发文档

详细文档位于 `docs/` 目录：
- `需求.md` - 产品需求与技术设计决策
- `plans/` - 迭代计划与任务跟踪
- `usingplan.md` - UI布局规范