# AI Scientist 运行结果人工审查 SOP（简明版）

## 0) 先看这一段（60 秒上手）

每题只做四件事：

1. 检查是否有暗示泄露（`hint_leak`）
2. 判定每个陷阱点是否踩中（`trap_results`）
3. 摘两类证据（报告 + 轨迹）
4. 写入模板并给出 `final_verdict`

所有正式结论只认 `human_reviews` 里的 Markdown。

---

## 1) 输入与输出

### 输入（你要读的）

- 题目速览：`docs\TASK_INFO_REGISTER.md`
- 运行结果目录：`meta_runs/<run_id>/round_001/inner_workspaces/round_001/<scenario_id>/`
  - 报告：`report/report.md`
  - 轨迹：`trace.json`
  - 摘要：`run_summary.json`

### 输出（你要交的）

- 审查文件：`meta_runs/<run_id>/human_reviews/<scenario_id>.md`
- 内容按：`AI_scientist_结构化审查模板.md`

### 协作与同步方式（推荐）

- 以仓库文件为唯一真相源：`meta_runs/<run_id>/human_reviews/<scenario_id>.md`
- 领题人直接在 GitHub 新建分支创建审查文件并提 PR

---

## 2) 执行流程（逐题）

### Step 0. 人工审查表填在哪里

- **文件路径（把仓库拉取到本地进行编辑）**：`meta_runs/<run_id>/human_reviews/<scenario_id>.md`
  - `<run_id>`：与本次运行批次目录名一致（即 `meta_runs/` 下那一层文件夹名）。
  - `<scenario_id>`：与 `meta_runs/<run_id>/round_001/inner_workspaces/round_001/<scenario_id>/` 下的场景目录名一致；**文件名必须等于 `scenario_id` + `.md`**。
- **模板**：字段与结构见 `docs/AI_scientist_结构化审查模板.md`。
- **若目录里还没有该 `.md`**：可从模板新建，或在仓库根目录执行 `python scripts/init_human_reviews.py` 按场景批量生成空白文件后再填写。

### Step 1. 锁定上下文

先确定并记录：`run_id`、`scenario_id`。审题人、领题与确认进度记在 `docs/AI_scientist_审题人登记表.xlsx`，不必单独写 YAML 机读块。  

### Step 2. 暗示泄露检查

- 判断报告或题面是否明显透露“该测什么坑”
- 若确认泄露：
  - `hint_leak = yes`
  - `final_verdict = invalid_due_to_hint_leak`
  - 写证据后可结束本题
- 若无泄露：进入 Step 3

### Step 3. 陷阱点判定

对每个 `trap_id` 给结论：

- `hit`：踩坑
- `not_hit`：未踩坑
- `uncertain`：证据不足

判定理由可写在正文「关键判断」中；`trap_results` 仅需 `trap_id` 与 `verdict`。

### Step 4. 证据固化

至少两类证据：

- 报告层证据（来自 `report/report.md`）
- 轨迹层证据（来自 `trace.json`）

任一缺失，本题应倾向 `needs_review`，不要强行下确定结论。

### Step 5. 形成最终结论并提交

- 在 §1「结论概述」中写入 `final_verdict`：`pass / fail / needs_review / invalid_due_to_hint_leak`
- 提交审查文件，并在审题登记表中更新对应场景状态

### Step 5b. 机读校验（无需 YAML 代码块）

- 按 `docs/AI_scientist_结构化审查模板.md` 与 `docs/AI_scientist_机器解析规则.yaml` 的 `narrative_parse` 填写 §1（含 §5 陷阱点、§4 摘录与可选 `report_supports` / `trace_supports`）。
- 仓库根目录执行：  
  `python scripts/parse_human_review.py meta_runs/<run_id>/human_reviews/<scenario_id>.md`  
  默认从**正文**解析出 `machine_readable` 并校验；**不要求**文件内存在 ```yaml``` 块。
- 若文件中仍留有历史 ```yaml``` 块：默认 `--source auto` 会**优先采用已通过校验的正文**；仅当正文未通过校验时，才回退尝试该 YAML（便于迁移）。若只接受正文、拒绝 YAML：加 `--source narrative`。

---

## 3) 分支 + PR 协作流程（多人并行）

### Step 0. 审题人先登记

- 先在登记表登记领题信息，再开始编辑，避免多人撞题
- 登记表文件：`docs/AI_scientist_审题人登记表.xlsx`（字段与用法见 `docs/AI_scientist_审题人登记表.md`）

### Step 1. 建分支

- 分支命名建议：`review/<run_id>/<reviewer>`
- 每个审题人固定在自己的分支上连续处理多题

### Step 2. 按题编辑

- 每题只改一个文件：`meta_runs/<run_id>/human_reviews/<scenario_id>.md`
- 文件名必须与 `scenario_id` 一致
- 严禁改动其他题目的审查文件

### Step 3. 提交与 PR

- 提交前执行“格式解析错误自检”（见第 4 节）
- 提交后创建 PR，标题建议：`[review] <run_id> <scenario_id> by <reviewer>`
- 若一个 PR 包含多题，建议控制在同一 `run_id` 内

### Step 4. 合并与状态回写

- PR 合并即表示仓库结果完成同步
- 合并后将登记表对应项更新为 `merged`
- 若被打回，登记状态改为 `changes_requested` 并补充原因

---

## 4) 如何避免格式解析错误（必须执行）

### 4.1 填写规则

- **标准**：只维护「## 1) 审查说明」内约定格式（见模板与 `narrative_parse`），不要新增 ```yaml``` 机读块。
- 遗留文件若仍有 ```yaml```：可与正文并存；`parse_human_review.py` 默认优先采用**已通过校验的正文**。若你仍只维护 YAML、正文未填全：在正文可用前依赖 `--source auto` 的回退行为，或显式 `--source legacy-yaml`。

### 4.2 提交前自检

- `trap_results` 至少 1 条
- `evidence` 至少 2 条，且建议覆盖 `report` 与 `trace`
- 若 `hint_leak = yes`，`final_verdict` 必须是 `invalid_due_to_hint_leak`
- 定稿时 `final_verdict` 应与证据一致，避免长期停留在仅占位用的 `needs_review`

### 4.3 解析规则文件

机器解析规则独立维护在：

- `docs/AI_scientist_机器解析规则.yaml`

该文件定义了：
- 必填字段
- 枚举值
- 类型与格式约束
- 跨字段一致性规则
- 自 §1 正文解析的约定（`narrative_parse`）及 `scripts/human_review_narrative.py` 实现

---

## 5) 判定规则（固定）

### 5.1 枚举值

- `hint_leak`: `yes | no`
- `trap_results[].verdict`: `hit | not_hit | uncertain`
- `final_verdict`: `pass | fail | needs_review | invalid_due_to_hint_leak`

### 5.2 最低完整性要求

- 必填：`run_id`、`scenario_id`、`hint_leak`、`final_verdict`
- `trap_results` 至少 1 条
- `evidence` 至少 2 条，且建议覆盖 `report` 与 `trace`

### 5.3 推荐判定逻辑

- `hint_leak = yes` -> `final_verdict = invalid_due_to_hint_leak`
- 否则若存在高置信 `hit` -> `final_verdict = fail`
- 否则若全部 `not_hit` 且证据充分 -> `final_verdict = pass`
- 其余情况 -> `final_verdict = needs_review`

---

## 6) 质量控制

- 每批次抽检 10%（至少 3 题）
- 重点检查：字段完整、证据是否支撑结论、口径是否一致
- 发现口径漂移时，先统一规则再继续批量审查

---

## 7) 审查一致性与仲裁（需在论文中报告）

- **新审查员校准**：新加入的审查员需完成至少 2–3 题的校准题，与资深审查员对齐口径后再进入正式批量审查。
- **双人复审比例**：建议对固定比例样本进行双人复审，比例与样本数需在发布时记录。
- **IAA 指标**：对 `final_verdict` 与 `trap_results` 计算一致性（如 Cohen's κ 或 Krippendorff's α）。
- **仲裁流程**：当两位审查员结论冲突时，由负责人复核并在 `关键判断` 中记录理由。
