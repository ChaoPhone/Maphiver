---
agent_rules:
  branch_naming:
    pattern: "{prefix}/{description}"
    pattern_with_issue: "{prefix}/{issue_id}-{description}"
    format: 全小写，单词用中划线分隔，禁止下划线/驼峰/中文/特殊字符
    prefixes:
      feature: 新增功能
      fix: 问题修复（必须关联 Issue）
      refactor: 架构优化/代码重构
  issue_requirement:
    condition: 创建 fix/ 分支前
    action: 必须先确认对应 Issue 已存在；若不存在，必须先创建 Issue 再创建分支
    issue_format: 标题以 [fix] 前缀开头，正文包含复现步骤、期望行为、实际行为
  branch_lifecycle:
    - git checkout master && git pull
    - "git checkout -b {prefix}/{issue_id}-{desc}（fix）或 {prefix}/{desc}（feature/refactor）"
    - 在分支内开发，仅做该分支目标事项
    - 本地验证通过后，合并到 master 并删除分支
  merge_constraint:
    target: master
    pre_merge: 必须本地验证代码可正常运行
    post_merge: 立即删除临时分支
    forbidden: 禁止直接在 master 上做功能开发、bug修复、架构优化
    exception: 仅文案错别字、注释修正、单参数微调等零风险改动可直接在 master 修改
  single_responsibility:
    principle: 一个分支只做一类改动、一个明确目标
    forbidden: 禁止在 feature 分支中改 bug、禁止在 fix 分支中做架构调整
  issue_close:
    action: fix 分支合入 master 后，必须在合并消息或 commit 中包含 Close #{issue_id} 以自动关闭 Issue
  refactor_long_cycle:
    condition: 重构跨模块且周期超过 1 周
    action: 创建集成分支 refactor/{desc}，所有改动在集成分支验证通过后再合入 master
---

# 贡献规范

本文档定义了 Maphiver 项目的分支管理与 Issue 规范。所有贡献者（包括 AI Agent）必须遵守。

## 一、核心原则

1. **唯一稳定基线**：仅保留 `master` 一个长期分支，永远保持可拉取、可部署、可运行。
2. **单分支单职责**：一个分支只做一类改动、一个目标，绝不混改。
3. **用完即删**：临时分支合入 `master` 后立即删除，不保留僵尸分支。

---

## 二、分支命名

格式：`<前缀>/<描述>` 或 `<前缀>/<Issue序号>-<描述>`

- 全小写字母，单词间用 `-` 中划线分隔
- 禁止下划线、驼峰、中文、特殊字符

---

## 三、三类改动与分支规范

### 1. 新增功能 → `feature/`

适用：所有新功能、新模块、原有功能的正向扩展。

| 规则 | 说明 |
|------|------|
| 拉取来源 | 最新 `master` |
| 合入目标 | `master`（功能验证可运行后） |
| 命名示例 | `feature/tts-voice-converter` |

约束：一个分支只做一个功能，不混改 bug、不做架构调整。

### 2. 问题修复 → `fix/`

适用：所有 bug 修复（报错、异常、逻辑错误等）。

| 规则 | 说明 |
|------|------|
| **前置要求** | **必须先有 Issue**，无 Issue 则先创建 |
| 拉取来源 | 最新 `master` |
| 合入目标 | `master`（验证 bug 已修复、不影响核心功能后） |
| 命名格式 | `fix/<Issue序号>-<描述>` |
| 命名示例 | `fix/42-api-timeout-retry` |
| 合入时 | commit 或合并消息中写 `Close #42` 自动关闭 Issue |

**Issue 模板**：
- 标题以 `[fix]` 开头，如 `[fix] 问答接口超时无重试`
- 正文包含：复现步骤 → 期望行为 → 实际行为

**唯一例外**：文案错别字、注释修正、单参数微调等零风险改动，可直接在 `master` 修改，修改后立即验证。

### 3. 架构优化 → `refactor/`

适用：代码重构、模块调整，不改变原有功能、不新增功能、不修 bug。

| 规则 | 说明 |
|------|------|
| 拉取来源 | 最新 `master` |
| 合入目标 | `master`（全量验证所有模块正常运行后） |
| 命名示例 | `refactor/qa-service-structure` |

**长周期重构**（跨模块、超过 1 周）：创建集成分支，验证通过后统一合入 `master`。

```
refactor/global-v2-arch-upgrade   ← 集成分支，最终合入 master
```

---

## 四、操作流程

```
1. 更新主线    git checkout master && git pull
2. 创建分支    git checkout -b <prefix>/<desc>
3. 开发验证    只做该分支目标事项，完成后本地全量验证
4. 合入清理    合入 master，删除临时分支
```

---

## 五、红线（不可突破）

1. **禁止**直接在 `master` 上做功能开发、bug 修复、架构优化。
2. **禁止**一个分支内混合多类改动。
3. **禁止**合入未经本地运行验证的代码到 `master`。
