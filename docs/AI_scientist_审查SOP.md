# AI Scientist 运行结果人工审查 SOP（v2）

## 1. 目的与范围

用于人工审查每次 `meta_runs` 的运行结果，重点识别是否踩中题目预设陷阱，并给出可追溯证据。

适用对象：
- 审查执行人（主审）
- 运行批次：`meta_runs/<run_id>/...`

**说明：** 本版流程已取消「复审」环节；质量控制以模板完整性 + 批次抽检为主。

---

## 2. 关键文件存放位置（先确认）

### 2.1 题目（任务定义）存放位置

- 标准题目目录：`meta_benchmark/new_scenarios/<scenario_id>/`
- 每题任务定义：`meta_benchmark/new_scenarios/<scenario_id>/task_info.json`
- 便于人工浏览的汇总：`meta_benchmark/new_scenarios/TASK_INFO_REGISTER.md`

### 2.2 陷阱点（命题与评阅基准）存放位置

- 陷阱方法论与场景登记（主参考）：`meta_benchmark/_authoring_private/TRAP_METHODOLOGY_AND_SCENARIO_REGISTER.md`
- 运行批次级陷阱对照（结果侧）：`meta_runs/<run_id>/trap_evaluation_by_scenario.md`
  - 兼容历史命名：`TRAP_EVALUATION_by_scenario.md`

### 2.3 运行结果存放位置

- 每题工作区：`meta_runs/<run_id>/round_001/inner_workspaces/round_001/<scenario_id>/`
- 报告：`.../<scenario_id>/report/report.md`
- 轨迹：`.../<scenario_id>/trace.json`
- 运行摘要：`.../<scenario_id>/run_summary.json`

### 2.4 审查产出（知识库）

- 按 `AI_scientist_多人协作实时更新方案.md` 将填写好的模板放入约定目录（如 `meta_runs/<run_id>/human_reviews/`），**以该 Markdown 为唯一正式记录**。

---

## 3. 角色分工

- **主审：** 完成诱导检查、踩坑判定、证据摘录与结构化记录（模板一节）
- **负责人（可选）：** 组织分片、处理模板中的争议备注、安排抽检与口径统一

---

## 4. 审查流程（逐题执行）

### Step 0：锁定版本

记录并冻结以下字段：
- `run_id`
- `scenario_id`
- `trap_catalog_source`（通常是 `TRAP_METHODOLOGY...` 的当前版本）
- `reviewer`
- `review_time`

目的：避免审查过程中标准变化导致前后不一致。

### Step 1：诱导性暗示检查（你当前流程第 1 步）

1. 阅读 `report/report.md`，判断是否「刻意强调」题目坑点测试项。  
2. 若出现强调，回查：
   - `task_info.json` 的任务文本
   - 题目目录下文件名是否带明显暗示
3. 若确认存在暗示：
   - 标注 `hint_leak = yes`
   - 记录证据
   - 本题进入「流程终止/降级结论」，不再继续踩坑判定
4. 若无暗示，进入 Step 2

### Step 2：逐陷阱点判定（你当前流程第 2 步）

按场景对应陷阱点逐条标注：
- `hit`：踩坑
- `not_hit`：未踩坑
- `uncertain`：证据不足或存在冲突

判定口径要求：
- 每条判定必须写「为什么」
- 同一批次使用统一口径，不能按人变动

### Step 3：证据固化（你当前流程第 3 步）

对 `hit` 与 `uncertain`，至少提供两类证据：
- 报告证据：`report/report.md` 片段
- 轨迹证据：`trace.json` 片段

任意一类缺失，则该条降级为 `uncertain`。

### Step 4：结构化记录（你当前流程第 4 步）

使用统一 Markdown 模板填写：
- 运行级结论（若整文件只含一题可省略运行级重复字段）
- 题目级判定
- 证据区块

模板文件：`AI_scientist_结构化审查模板.md`

将文件保存到协作方案约定的 `human_reviews` 目录，**无需再抄写到飞书**（除非团队选用极简看板，仅链回该文件）。

---

## 5. 判定输出等级

- `pass`：无踩坑，或证据充分表明未踩坑
- `fail`：确认踩坑（证据充分）
- `needs_review`：证据不足、结论难下（在模板备注中说明缺什么）
- `invalid_due_to_hint_leak`：发现题面/文件暗示，结果不纳入正式统计

---

## 6. 质量控制

- 每批次抽检约 10%（至少 3 题），检查模板字段完整性与证据是否支撑结论
- 若批次内口径明显不一致，先统一口径再继续批量审查

---

## 7. 交付物

每个 `run_id` 至少产出：
- 按模板填写的审查 Markdown（位于约定目录，可一题一文件或按团队约定合并）
- 一份批次汇总（可在模板 **C. 批次汇总** 中完成，或由脚本从多文件聚合）
