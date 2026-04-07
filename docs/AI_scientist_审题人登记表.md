# AI Scientist 审题人登记表（说明）

正式登记表为 Excel 文件：**`docs/AI_scientist_审题人登记表.xlsx`**

## 结构

- **每个运行批次一个工作表（sheet）**，sheet 名对应批次 `run_id`。  
  Excel 对工作表名最长 **31 个字符**，超长时会自动截断；**完整批次名**始终写在每个 sheet 的 **`B1`**。
- **每一列**对应一个 **`scenario_id`**（场景），列名在表头第 2 行。
- **固定行（从第 3 行起）**填写该场景下的登记信息：
  - **审题人**：负责审查该场景的人员标识（与 GitHub 账号或约定昵称一致即可）
  - **领题时间**：认领本题的时间（建议 `YYYY-MM-DD HH:mm`）
  - **提交审查时间**：完成 `human_reviews/<scenario_id>.md` 并提交 PR 的时间
  - **负责人确认时间**：负责人确认合并或口径无误的时间
  - **状态**：本题在登记流程中的阶段，仅使用以下三种取值之一  
    - `已领`：已认领，审查尚未完成  
    - `已审`：审题人已完成审查文件与 PR（或待负责人过目）  
    - `负责人已确认`：负责人已确认，可作为该场景登记闭环

第 7 行为状态取值提示（与上表一致）。

## 重新生成列（场景）

新增批次或 `meta_runs` 下场景目录变化后，可在仓库根目录执行：

```bash
python scripts/generate_reviewer_register_xlsx.py
```

脚本会扫描 `meta_runs/<run_id>/round_001/inner_workspaces/round_001/` 下的子目录名作为 `scenario_id`，**覆盖生成** `docs/AI_scientist_审题人登记表.xlsx`。若 sheet 已手工填写，请先备份再运行。

## 与审查文件的关系

- 登记表的「状态」只表示**协作与确认进度**；**审查结论**仍以 `meta_runs/<run_id>/human_reviews/<scenario_id>.md` 中 `machine_readable` 为准。
