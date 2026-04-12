# PRD: 流式知识河 - Notion 风格三栏布局

## 目标
打造"干净、学术、去UI化"的沉浸式阅读体验，实现"上传→解析→阅读→划词提问→流式回答→知识卡片"的完整闭环，解决 LaTeX 矩阵公式破版问题。

## 用户故事
作为学习者，我想在同一页面完成文档上传、阅读、划词提问、查看AI回复、管理知识卡片，并获得类似 Notion 的极简沉浸体验，以便专注学习不被 UI 干扰。

---

## 视觉规范 (Design Tokens)

### 色彩体系
| 变量 | 值 | 用途 |
|------|-----|------|
| --bg-main | #FFFFFF | 中栏正文区，极致纯粹 |
| --bg-sidebar | #F7F7F9 | 左栏与右栏，微妙灰白层次 |
| --bg-hover | #EFEFF1 | 按钮和列表悬停反馈 |
| --text-primary | #1A1A1A | 正文，高对比度易读 |
| --text-secondary | #737373 | 次要信息、面包屑、时间 |
| --text-accent | #2563EB | 提问按钮、高亮选区（学术蓝） |
| --border-color | rgba(0,0,0,0.06) | 极淡分割线 |

### 字体排版
- 正文：系统字体栈（-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto...）
- 行高：1.75
- 字号：正文 16px，辅助信息 13-14px
- 段落间距：1.5em

---

## 需求分类

### Must（必须）
1. **三栏弹性布局**：左栏260px（可折叠）、中栏flex:1（min-width:600px + padding:10vw）、右栏360px（条件显示）
2. **全局 CSS 变量**：建立视觉规范，覆盖 Element Plus 默认样式
3. **中栏沉浸设计**：去除边框，段落直接渲染，两侧留白
4. **划词提问交互**：选中文字后右栏自动展开，正文保持高亮
5. **AI 回复极简渲染**：纯文本流，无聊天气泡，Markdown+LaTeX
6. **LaTeX 换行符保护**：解决矩阵公式破版问题
7. **知识卡片无缝生成**：原地展开输入框，无弹窗打断

### Should（应该）
1. **隐形面包屑**：滚动位置动态显示当前章节
2. **历史问答折叠**：右栏底部可折叠查看
3. **学习足迹时间线**：左栏底部显示

### Could（可选）
1. 多文档关联阅读
2. 导出功能

---

## 验收标准（Given-When-Then）

### V1: 视觉规范
- Given: 用户进入 Read 视图
- When: 页面加载完成
- Then: 背景分层显示（#FFFFFF/#F7F7F9），边框极淡，正文高对比度

### V2: 弹性布局
- Given: 用户调整窗口大小
- When: 窗口宽度变化
- Then: 中栏自适应，左/右栏宽度固定，无公式破版

### V3: 上传解析流程
- Given: 用户进入 Read 视图
- When: 用户上传 PDF 文件
- Then: 中栏流式显示解析进度和格式化后的文档内容

### V4: 划词提问流程
- Given: 文档已解析完成
- When: 用户选中一段文字
- Then: 右栏自动展开，正文保持高亮，显示操作按钮

### V5: AI 回复流程
- Given: 用户点击"向 AI 提问"
- When: AI 开始生成回复
- Then: 右栏流式显示纯文本流（无气泡），Markdown+LaTeX 正确渲染

### V6: LaTeX 稳定性
- Given: AI 返回含矩阵的公式
- When: 流式渲染完成
- Then: 矩阵公式正确显示，无换行符丢失

### V7: 知识卡片无缝生成
- Given: 用户点击"摘录为知识卡"
- When: 输入批注并 Enter
- Then: 原地显示"✅ 已汇入知识河"，无弹窗打断

---

## 技术约束
- 前端：Vue3 + TypeScript + Element Plus + 纯 Flexbox
- 后端：FastAPI + DeepSeek API（流式）
- 公式渲染：KaTeX + 换行符保护逻辑
- 划词组件：自定义实现（window.getSelection）
- 样式：CSS 变量 + scoped CSS + 深度选择器覆盖 Element Plus