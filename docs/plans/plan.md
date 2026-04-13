# Plan: Notion 风格三栏弹性布局优化

**版本**: v2.0
**最后更新**: 2026-04-13
**状态**: 已完成

## 任务列表

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

## 实现文件

| 文件 | 说明 |
|------|------|
| `frontend/src/styles/variables.css` | 全局 CSS 变量（Design Tokens） |
| `frontend/src/utils/latex.ts` | LaTeX 换行符保护逻辑 |
| `frontend/src/views/Read.vue` | Notion 风格三栏布局 |
| `frontend/src/main.ts` | 导入全局样式 |

## 变更记录
- 2026-04-12: 初始规划（v1.0），参考Streamlit版本设计
- 2026-04-13: 完成三栏布局基础实现（v1.0）
- 2026-04-13: 变更请求 - Notion 风格优化，参考 changelog/2026-04-13_notion-style-layout.md（v2.0）
- 2026-04-13: 完成所有 N1-N9 任务，提交 commit 9f39c01