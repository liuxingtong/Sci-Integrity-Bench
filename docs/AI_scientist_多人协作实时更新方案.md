# AI Scientist 多人协作与实时更新方案（轻量可落地）

## 1. 协作目标

在不改动现有运行产物目录结构的前提下，实现：
- 多人并行审查不冲突
- 审查进度可查、结论可追溯
- **以结构化 Markdown 为唯一事实来源**，减少重复录入

---

## 2. 推荐架构（默认：知识库 + Git）

采用「原始数据轨 + 审查记录轨」：

| 轨道 | 内容 | 说明 |
|---|---|---|
| 原始数据轨 | 题目、陷阱文档、运行结果 | 路径见下文，一般不手改 |
| 审查记录轨 | 按模板填写的 Markdown | **放入仓库固定目录**，即团队知识库 |

**飞书多维表不是必需。** 若团队习惯用在线表做看板，可选用下文「可选：极简飞书」；否则只维护仓库里的 md 即可，汇总用脚本扫目录 + 解析模板字段（或定期导出快照 md）。

---

## 3. 数据放置约定（与现有仓库对齐）

### 3.1 原始数据轨（不手改）

- 题目：`meta_benchmark/new_scenarios/<scenario_id>/task_info.json`
- 陷阱：`meta_benchmark/_authoring_private/TRAP_METHODOLOGY_AND_SCENARIO_REGISTER.md`
- 运行结果：`meta_runs/<run_id>/round_001/inner_workspaces/round_001/<scenario_id>/...`

### 3.2 审查记录轨（知识库，主协作面）

建议目录（可按项目习惯二选一或并存）：

- `meta_runs/<run_id>/human_reviews/` — 与单次运行绑定；或
- `docs/human_reviews/<run_id>/` — 与文档放一起

**命名约定（便于自动汇总）：**

- 每个 `scenario_id` 一个文件：`{scenario_id}.md`，内容使用 `AI_scientist_结构化审查模板.md` 中 **单题一节** 的结构；**或**
- 每个审查员一个文件：`{reviewer}_{scenario_id}.md`，避免多人改同一文件。

同一 `scenario_id` 最终只保留一份定稿时，可合并为 `{scenario_id}.md` 或由负责人覆盖。

---

## 4. 从 Markdown 自动提取到统计（原则）

模板中已使用固定键名（如 `hint_leak`、`final_verdict`、`trap_id` 等），可用简单脚本按行或按 YAML 块解析，**无需在飞书里再抄一遍**。

若日后需要同步到飞书，优先做「脚本：扫描 `human_reviews` → 写多维表」，而不是人工填表。

---

## 5. 可选：极简飞书（仅在看板需要时）

若仍使用在线表，建议 **不超过** 下列字段（能自动的都不要手填）：

| 字段名 | 说明 |
|---|---|
| run_id | 运行批次 |
| scenario_id | 题目编号 |
| doc_link | **仓库内 md 路径或提交链接**（唯一必填的人工关联） |
| owner | 当前谁在看（领取人，可选） |
| status | `todo / in_progress / done` |

其余结论类字段一律以仓库 md 为准，不在表中维护。

---

## 6. 状态流转（简化）

`todo → in_progress → done`

- `hint_leak = yes` 时本题可直接 `done`（结论见模板中的 `invalid_due_to_hint_leak`）
- 不再设「复审 / 仲裁」状态；有争议时在模板备注中说明，由负责人抽检或例会处理

---

## 7. 分工与防撞单

- 分片：按 `scenario_id` 前缀或按 `run_id` 切分
- 领取方式：在文件名或目录 README 中声明 owner，或仅用「每人独占文件」避免 Git 冲突
- 长时间未动：在对应 md 或目录 README 备注转交原因即可

---

## 8. 定期快照（建议）

每天或每批次结束时，将 `human_reviews/` 下文件列表与可选脚本汇总写入：

- `meta_runs/<run_id>/review_progress_snapshot_YYYYMMDD.md`

内容可包括：已完成题数、`final_verdict` 分布、需关注项（如 `needs_review`）。**内容由脚本从 md 生成，人只审阅快照。**

---

## 9. 配套文档

- 执行规范：`AI_scientist_审查SOP.md`
- 批改模板：`AI_scientist_结构化审查模板.md`
- 协作规则：本文件

以上文档固定后，建议仅在流程变更时更新版本并简短记录变更说明。
