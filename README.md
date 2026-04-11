# 流式知识河 (Streaming Knowledge River)

一个以**对话流驱动、注重知识点自然关联与沉淀**的本地化AI学习伴侣。

## 项目简介

**目标用户**：理工科大学生（高等数学、线性代数、大学物理学习场景）

**核心痛点**：
- 阅读教材时存在概念理解障碍，读不懂、记不住
- 学后知识呈碎片化，无法有效关联新旧知识
- 传统AI对话难以把握整体知识结构
- 缺乏对"不懂"和"犯错"知识点的沉淀与回顾机制

**产品愿景**：让学习者在与AI的自由问答中，自然形成结构化的知识脉络，并专属保存认知突破时刻的"知识财富"。

## 技术栈

- **前端框架**：Streamlit（单体应用架构）
- **AI服务**：DeepSeek API（流式输出）
- **数据库**：SQLite（本地存储）
- **PDF解析**：PyMuPDF (fitz)
- **公式渲染**：MathJax/KaTeX

## 文档架构

```
e:\project\Maphiver\
├── 需求.md          # 产品需求 + 技术设计决策（Why + How）
├── agent计划.md     # 迭代任务拆解（AX/BX 任务清单）
├── README.md        # 项目简介 + 文档导航
└── maphiver/        # 源代码目录
    ├── app.py       # Streamlit 应用入口
    ├── services/    # 业务逻辑层
    ├── models/      # Pydantic 数据模型
    └── repositories/ # SQLite 数据访问
```

### 文档职责

| 文件 | 职责 | 内容 |
|------|------|------|
| **需求.md** | 产品定义 + 技术约束 | 用户故事、功能需求(F-01~F-10)、非功能需求、技术设计决策、MVP验收清单 |
| **agent计划.md** | 任务执行 | A0-A5 初始化任务（Agent执行）、B3.1-B3.2 问题修复与优化（人类补充） |
| **README.md** | 项目导航 | 项目简介、技术栈、文档架构说明 |

## 快速启动

```bash
cd maphiver
pip install -r requirements.txt
python -m streamlit run app.py --server.port 8511
```

## 核心功能

1. **PDF上传与解析**：支持高等数学、线性代数等含公式文档
2. **AI初始解答**：上传后自动生成详细解答作为学习起点
3. **流式问答**：选中文本后进行上下文感知问答
4. **知识卡片**：一键摘录AI回答，添加批注保存
5. **学习足迹**：自动记录提问轨迹，生成探索路径图
6. **历史恢复**：归档会话可完整恢复

## 数据模型

5张核心表：
- `documents` - 文档元数据
- `sessions` - 会话生命周期（draft/archived）
- `messages` - 问答记录
- `knowledge_cards` - 摘录批注
- `footprints` - 学习足迹