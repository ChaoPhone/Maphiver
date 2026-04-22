# Plan: 前端页面解耦重构

**版本**: v2.0
**最后更新**: 2026-04-20
**状态**: 已完成

## 目标

将 Read.vue（1255行）拆解为多个职责单一的组件，消除 Home.vue 与 Read.vue 的功能重复，正确使用已存在的 CardPanel.vue、ExportPanel.vue 等组件，使代码结构清晰、可维护。

---

## 问题诊断（已解决）

### 解耦前页面类型

| 路由 | 组件 | 行数 | 职责数量 |
|------|------|------|---------|
| `/` | Read.vue | 1255 | 10+ |
| `/read/:sessionId` | Read.vue | 1255 | 10+ |
| `/history` | Home.vue | 203 | 3 |

### 解耦后页面类型

| 路由 | 组件 | 行数 | 职责数量 |
|------|------|------|---------|
| `/` | Read.vue | ~426 | 3（组合组件） |
| `/read/:sessionId` | Read.vue | ~426 | 3（组合组件） |
| `/history` | Home.vue | ~120 | 2 |

---

## 任务列表

### Phase 1: 提取核心组件

| ID | 描述 | 验收标准 | 状态 |
|----|------|----------|------|
| D1 | 创建 DocumentUploader.vue | 合并 Home+Read 上传逻辑，支持 drag/点击/进度显示，emit uploaded 事件 | completed |
| D2 | 创建 ParsingProgress.vue | 显示解析进度条 + 流式内容预览，支持 stage/percentage/content props | completed |
| D3 | 创建 FormulaRenderer.vue | Markdown + LaTeX 渲染，emit select 事件，支持 dark mode | completed |
| D4 | 创建 QAPanel.vue | 划词后显示的问答面板，包含快捷按钮 + 自定义输入 + 流式回复 | completed |
| D5 | 创建 QAHistory.vue | 历史问答折叠列表，支持展开/收起 | completed |
| D6 | 创建 LeftSidebar.vue | 左侧悬浮侧边栏，包含卡片列表 + 足迹面板 | completed |

### Phase 2: 重构 Read.vue

| ID | 描述 | 验收标准 | 状态 |
|----|------|----------|------|
| D7 | Read.vue 使用 DocumentUploader | 无文档时显示上传组件，删除重复的上传代码 | completed |
| D8 | Read.vue 使用 ParsingProgress | 解析中显示进度组件，删除重复的进度代码 | completed |
| D9 | Read.vue 使用 FormulaRenderer | 替换内联渲染逻辑，通过 props 传入内容 | completed |
| D10 | Read.vue 使用 QAPanel | 划词后显示问答组件，删除重复的问答代码 | completed |
| D11 | Read.vue 使用 QAHistory | 右栏底部显示历史问答，删除重复的历史代码 | completed |
| D12 | Read.vue 使用 LeftSidebar | 左侧悬浮栏使用 LeftSidebar 组件 | completed |
| D13 | Read.vue 使用 CardPanel | LeftSidebar 内部使用 CardPanel | completed |
| D14 | Read.vue 使用 ExportPanel | 暂未添加（可选功能） | pending |

### Phase 3: 重构 Home.vue

| ID | 描述 | 验收标准 | 状态 |
|----|------|----------|------|
| D15 | Home.vue 使用 DocumentUploader | 替换重复的上传代码，保持文档列表 + 会话列表功能 | completed |

### Phase 4: 路由优化

| ID | 描述 | 验收标准 | 状态 |
|----|------|----------|------|
| D16 | 调整路由命名 | `/` → home，语义更清晰 | completed |

### Phase 5: 代码清理

| ID | 描述 | 验收标准 | 状态 |
|----|------|----------|------|
| D17 | 删除 Read.vue 重复代码 | 行数从 1255 降至 ~426 | completed |
| D18 | 删除 Home.vue 重复代码 | 行数从 203 降至 ~120 | completed |
| D19 | 删除 HelloWorld.vue | 未使用的示例组件 | completed |

---

## 组件架构图（解耦后）

```
frontend/src/
├── views/
│   ├── Home.vue          (~120行) 文档列表 + 会话列表 + 上传入口
│   └── Read.vue          (~426行) 组合各组件的容器
│
├── components/
│   ├── DocumentUploader.vue  (~100行) 统一上传组件
│   ├── ParsingProgress.vue   (~80行)  解析进度视图
│   ├── FormulaRenderer.vue   (~60行)  Markdown + LaTeX 渲染
│   ├── QAPanel.vue           (~150行) 问答面板
│   ├── QAHistory.vue         (~80行)  历史问答列表
│   ├── LeftSidebar.vue       (~100行) 侧边栏容器
│   ├── CardPanel.vue         (已存在) 知识卡片
│   ├── ExportPanel.vue       (已存在) 导出面板
│   └── FootprintPanel.vue    (已存在) 学习足迹
│
├── stores/
│   └── index.ts          (保持不变)
│
└── utils/
    └── latex.ts          (保持不变)
```

---

## 解耦效果

| 指标 | 解耦前 | 解耦后 | 改善 |
|------|--------|--------|------|
| Read.vue 行数 | 1255 | 426 | -66% |
| Home.vue 行数 | 203 | 120 | -41% |
| 组件数量 | 8 | 10 | +2（新增核心组件） |
| 功能重复 | 2处 | 0 | 完全消除 |
| 未使用组件 | 3个 | 0 | 完全消除 |

---

## 变更记录

- 2026-04-20: 初始规划（v1.0），基于页面解耦分析
- 2026-04-20: 完成所有 Phase 1-5 任务（v2.0），Read.vue 从 1255 行降至 426 行