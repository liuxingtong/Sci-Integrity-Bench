# AI Scientist 多人协作与实时更新方案（轻量可落地）

## 1. 协作目标

在不改动现有运行产物目录结构的前提下，实现：
- 多人并行审查不冲突
- 审查状态实时可见
- 结论可追溯、可回放

---

## 2. 推荐架构（最省事）

采用“双轨制”：
- 原始数据轨（Git/文件夹）：保存题目、陷阱文档、运行结果
- 协作状态轨（在线表）：保存审查状态、结论、证据链接

好处：原始文件稳定，协作更新快，不会多人改同一 md 导致冲突。

---

## 3. 数据放置约定（与现有仓库对齐）

### 3.1 原始数据轨（不手改）

- 题目：`meta_benchmark/new_scenarios/<scenario_id>/task_info.json`
- 陷阱：`meta_benchmark/_authoring_private/TRAP_METHODOLOGY_AND_SCENARIO_REGISTER.md`
- 运行结果：`meta_runs/<run_id>/round_001/inner_workspaces/round_001/<scenario_id>/...`

### 3.2 协作状态轨（实时更新）

建议建立一个在线表（飞书多维表/Notion/Airtable 任一），一行一个 `run_id + scenario_id`。

---

## 4. 在线表最小字段（直接照抄）

| 字段名 | 说明 | 示例 |
|---|---|---|
| run_id | 运行批次 | `new_deepseek-chat_no-reviewer_20260406_215418` |
| scenario_id | 题目编号 | `05c_CyberSecurity_IncidentNarrativeTriage` |
| trap_id | 对应陷阱 | `T05` |
| owner | 当前主审 | `alice` |
| reviewer2 | 复审人 | `bob` |
| status | 流程状态 | `todo/in_progress/reviewed/adjudicated/done` |
| lock_owner | 当前编辑锁 | `alice` |
| hint_leak | 是否暗示泄露 | `yes/no` |
| verdict | 判定 | `hit/not_hit/uncertain` |
| final_verdict | 最终状态 | `pass/fail/needs_review/invalid_due_to_hint_leak` |
| report_evidence | 报告证据摘要 | 文本 |
| trace_evidence | 轨迹证据摘要 | 文本 |
| conflict_flag | 是否冲突 | `yes/no` |
| updated_at | 最后更新时间 | 时间戳 |

---

## 5. 状态流转（建议固定）

`todo -> in_progress -> reviewed -> adjudicated -> done`

补充规则：
- `hint_leak = yes` 时可直接进入 `adjudicated`
- `verdict = uncertain` 自动打 `conflict_flag = yes`
- 只有 `lock_owner` 才能修改该行

---

## 6. 锁与分工机制（防撞单）

- 分片原则：按 `scenario_id` 前缀或按 `run_id` 切分
- 每人先“领取”再编辑：写入 `lock_owner`
- 超过 24 小时未更新可转交（需在备注写明原因）

---

## 7. 实时更新节奏

- 主审：开始审查即改 `status=in_progress`
- 完成首轮：10 分钟内写入 `verdict + evidence`
- 复审：只处理 `hit/uncertain`
- 仲裁：每天固定 1-2 次集中处理冲突项

---

## 8. 每日同步回仓（建议）

每天固定时刻将在线表导出为一个 Markdown 快照，命名：
- `meta_runs/<run_id>/review_progress_snapshot_YYYYMMDD.md`

快照包含：
- 各状态计数
- 当日新增 fail/uncertain
- 冲突清单与责任人

---

## 9. 配套文档建议

- 执行规范：`AI_scientist_审查SOP.md`
- 批改模板：`AI_scientist_结构化审查模板.md`
- 协作规则：本文件 `AI_scientist_多人协作实时更新方案.md`

以上三份文档固定后，建议每月仅改一次版本并记录变更说明。
