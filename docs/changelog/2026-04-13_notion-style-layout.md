# 变更记录：Notion 风格三栏弹性布局优化

**日期**: 2026-04-13
**决策者**: 用户确认
**变更原因**: 当前三栏布局存在视觉干扰，需要打造"干净、学术、去UI化"的沉浸式阅读体验，解决 LaTeX 矩阵公式破版问题。

---

## 变更概述

从"功能性三栏布局"升级为"Notion 风格的经典三栏弹性布局"，重点优化：
1. 全局视觉规范（CSS 变量）
2. 极简弹性布局架构
3. 核心组件交互设计
4. LaTeX 公式渲染稳定性

---

## 影响范围

| 类型 | 文件/模块 | 变更内容 |
|------|----------|----------|
| PRD | docs/prd.md | 新增"视觉规范"章节，更新验收标准 |
| Plan | docs/plans/plan.md | 新增 UI 重构任务项 |
| 前端样式 | frontend/src/styles/variables.css | 新建全局 CSS 变量文件 |
| 前端布局 | frontend/src/App.vue | 重构为纯 Flex 三栏布局 |
| 前端组件 | frontend/src/views/Read.vue | 去除边框、优化沉浸感 |
| 前端组件 | frontend/src/components/QAPanel.vue | 极简交互设计 |
| 前端工具 | frontend/src/utils/latex.ts | LaTeX 换行符保护逻辑 |

---

## 新旧对比

### 布局架构

| 维度 | 旧方案 | 新方案 |
|------|--------|--------|
| 布局方式 | Element Plus Container | 纯 Flexbox |
| 左栏宽度 | 240px 固定 | 260px，可折叠 |
| 中栏宽度 | flex:1 | flex:1 + min-width:600px + padding:10vw |
| 右栏宽度 | 320px 固定 | 360px，条件显示 |
| 背景 | 单色 | 分层背景（#FFFFFF / #F7F7F9） |

### 视觉规范

| 维度 | 旧方案 | 新方案 |
|------|--------|--------|
| 背景色 | 无规范 | CSS 变量定义 |
| 文本色 | Element Plus 默认 | 学术级对比度 |
| 边框 | Element Plus 默认边框 | 极淡分割线 rgba(0,0,0,0.06) |
| 字号 | 无规范 | 正文 16px，辅助 13-14px |
| 行高 | 无规范 | 1.75 |

### 交互设计

| 维度 | 旧方案 | 新方案 |
|------|--------|--------|
| 划词提问 | 弹出悬浮按钮 | 右栏自动展开 + 正文高亮 |
| AI 回复 | 聊天气泡样式 | 纯文本流，无气泡 |
| 知识卡片 | 弹窗输入批注 | 原地展开输入框 |
| 面包屑 | 无 | 滚动位置动态显示章节 |

---

## 技术方案

### 1. CSS 变量体系

```css
:root {
  --bg-main: #FFFFFF;
  --bg-sidebar: #F7F7F9;
  --bg-hover: #EFEFF1;
  --text-primary: #1A1A1A;
  --text-secondary: #737373;
  --text-accent: #2563EB;
  --border-color: rgba(0, 0, 0, 0.06);
}
```

### 2. LaTeX 换行符保护

```typescript
function safeLatexFormat(rawText: string): string {
  const latexRegex = /(\$\$[\s\S]*?\$\$|\$[\s\S]*?\$)/g;
  return rawText.replace(latexRegex, (match) => {
    return match.replace(/\\\\/g, '%%NEWLINE%%');
  });
}
```

### 3. 知识卡片无缝生成

点击"摘录为知识卡"后：
- 不弹窗，原地展开输入框
- Enter 保存，显示"✅ 已汇入知识河"
- 左栏静默更新卡片数量

---

## 验收标准

### V1: 视觉规范
- Given: 用户进入 Read 视图
- When: 页面加载完成
- Then: 背景分层显示，边框极淡，正文高对比度

### V2: 弹性布局
- Given: 用户调整窗口大小
- When: 窗口宽度变化
- Then: 中栏自适应，左/右栏宽度固定，无公式破版

### V3: LaTeX 稳定性
- Given: AI 返回含矩阵的公式
- When: 流式渲染完成
- Then: 矩阵公式正确显示，无换行符丢失

### V4: 知识卡片无缝生成
- Given: 用户点击"摘录为知识卡"
- When: 输入批注并 Enter
- Then: 原地显示成功提示，无弹窗打断

---

## 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Element Plus 样式覆盖冲突 | 中 | 使用 scoped CSS + 深度选择器 |
| LaTeX 保护逻辑遗漏边界情况 | 低 | 单元测试覆盖 |
| 窗口极小导致布局崩溃 | 低 | min-width 保护 |

---

## 回滚方案

1. 保留旧版 Read.vue 为 ReadLegacy.vue
2. 新版失败时切换路由指向旧版
3. Git revert 本次变更提交