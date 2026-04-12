# Plan: Notion 风格三栏弹性布局优化

**版本**: v2.0
**最后更新**: 2026-04-13
**状态**: 规划中

## 任务列表

| ID | 描述 | 验收标准 | 状态 |
|----|------|----------|------|
| N1 | 创建全局 CSS 变量文件 | variables.css 包含所有 Design Tokens | pending |
| N2 | 重构 App.vue 为纯 Flex 三栏布局 | 左260px/中flex:1/右360px，可折叠 | pending |
| N3 | 中栏沉浸设计优化 | 去除边框，padding:10vw，段落直接渲染 | pending |
| N4 | 划词提问交互优化 | 选中后右栏自动展开，正文保持高亮 | pending |
| N5 | AI 回复极简渲染 | 纯文本流，无气泡，Markdown+LaTeX | pending |
| N6 | LaTeX 换行符保护逻辑 | 矩阵公式正确显示，无破版 | pending |
| N7 | 知识卡片无缝生成 | 原地展开输入框，无弹窗 | pending |
| N8 | 隐形面包屑实现 | 滚动位置动态显示章节 | pending |
| N9 | Element Plus 样式覆盖 | 边框、阴影、按钮样式极简化 | pending |

## 变更记录
- 2026-04-12: 初始规划（v1.0），参考Streamlit版本设计
- 2026-04-13: 完成三栏布局基础实现（v1.0）
- 2026-04-13: 变更请求 - Notion 风格优化，参考 changelog/2026-04-13_notion-style-layout.md（v2.0）