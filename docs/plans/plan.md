# Plan: 前端交互全流程细化

**版本**: v3.0
**最后更新**: 2026-04-13
**状态**: 规划中

## 任务列表

### Phase 1: Notion 风格布局（已完成）

| ID | 描述 | 验收标准 | 状态 |
|----|------|----------|------|
| N1 | 创建全局 CSS 变量文件 | variables.css 包含所有 Design Tokens | completed |
| N2 | 重构 Read.vue 为纯 Flex 三栏布局 | 左260px/中flex:1/右360px，可折叠 | completed |
| N3 | 中栏沉浸设计优化 | 去除边框，padding:10vw，段落直接渲染 | completed |
| N4 | 划词提问交互优化 | 选中后右栏自动展开，正文保持高亮 | completed |
| N5 | AI 回复极简渲染 | 纯文本流，无气泡，Markdown+LaTeX | completed |
| N6 | LaTeX 换行符保护逻辑 | 矩阵公式正确显示，无破版 | completed |
| N7 | 知识卡片无缝生成 | 原地展开输入框，无弹窗 | completed |
| N8 | 隐形面包屑实现 | 滚动位置动态显示章节 | completed |
| N9 | Element Plus 样式覆盖 | 边框、阴影、按钮样式极简化 | completed |

### Phase 2: 交互流程细化（新增）

| ID | 描述 | 验收标准 | 状态 |
|----|------|----------|------|
| I1 | 首页上传流程实现 | 拖拽→上传→解析→跳转，进度条正确显示 | pending |
| I2 | 阅读页面初始化流程 | loading→内容流式显示→卡片加载→面包屑就绪 | pending |
| I3 | 划词提问流程实现 | 选区≥10字→popup→右栏展开→快捷按钮 | pending |
| I4 | 知识卡片无缝生成 | inline输入框→Enter保存→成功提示→列表更新 | pending |
| I5 | AI回复流式渲染 | SSE→逐字显示→LaTeX正确→摘录按钮 | pending |
| I6 | 面包屑导航实现 | IntersectionObserver→标题检测→淡入淡出 | pending |
| I7 | 左栏折叠/展开 | 按钮→宽度动画→中栏自适应 | pending |

## 实现文件

| 文件 | 说明 |
|------|------|
| `frontend/src/styles/variables.css` | 全局 CSS 变量（Design Tokens） |
| `frontend/src/utils/latex.ts` | LaTeX 换行符保护逻辑 |
| `frontend/src/views/Read.vue` | Notion 风格三栏布局 + 交互流程 |
| `frontend/src/views/Home.vue` | 首页上传流程 |
| `frontend/src/main.ts` | 导入全局样式 |

## 变更记录
- 2026-04-12: 初始规划（v1.0），参考Streamlit版本设计
- 2026-04-13: 完成三栏布局基础实现（v1.0）
- 2026-04-13: 变更请求 - Notion 风格优化，参考 changelog/2026-04-13_notion-style-layout.md（v2.0）
- 2026-04-13: 完成所有 N1-N9 任务，提交 commit 9f39c01
- 2026-04-13: 变更请求 - 前端交互全流程细化，参考 changelog/2026-04-13_frontend-interaction-flow.md（v3.0）