# AI Scientist 审题人登记表（说明）

正式登记表为 Excel 文件：**`docs/AI_scientist_审题人登记表.xlsx`**

## 结构

- **每个模型运行批次一个工作表（sheet）**，该批次下**全部题目**写在**同一张表**里（一行一题；含 11×3 的 abc 套题时共 **33 行数据**）。sheet 名对应批次 `run_id`。  
  Excel 对工作表名最长 **31 个字符**，超长时会自动截断；**完整批次名**始终写在每个 sheet 的 **`B1`**。
- **场景顺序**：按题号与 **a/b/c 轮换**排列，即 `01a, 01b, 01c, 02a, 02b, 02c, …`（解析自目录名前缀 `NNx_`）。若某批次只有 `*a_*` 等子集，则仅列出实际存在的目录。
- **表头在第 2 行**；**从第 3 行起**每一行对应一道 **`scenario_id`**，列依次为：
  - **序号**：1 起递增，便于清点总题数  
  - **scenario_id（场景）**：与 `inner_workspaces` 下目录名一致  
  - **审题人**：负责审查该场景的人员标识（与 GitHub 账号或约定昵称一致即可）
  - **领题时间**：认领本题的时间（建议 `YYYY-MM-DD HH:mm`）
  - **提交审查时间**：完成 `human_reviews/<scenario_id>.md` 并提交 PR 的时间
  - **负责人确认时间**：负责人确认合并或口径无误的时间
  - **状态**：本题在登记流程中的阶段，仅使用以下三种取值之一  
    - `已领`：已认领，审查尚未完成  
    - `已审`：审题人已完成审查文件与 PR（或待负责人过目）  
    - `负责人已确认`：负责人已确认，可作为该场景登记闭环

数据行下方一行为状态取值提示（与上表一致）。

## 重新生成列（场景）

新增批次或 `meta_runs` 下场景目录变化后，可在仓库根目录执行：

```bash
python scripts/generate_reviewer_register_xlsx.py
```

脚本会扫描 `meta_runs/<run_id>/round_001/inner_workspaces/round_001/` 下的子目录名作为 `scenario_id`，**覆盖生成** `docs/AI_scientist_审题人登记表.xlsx`。若 sheet 已手工填写，请先备份再运行。

## 与审查文件的关系

- 登记表的「状态」只表示**协作与确认进度**；**审查结论**仍以 `meta_runs/<run_id>/human_reviews/<scenario_id>.md` 中 `machine_readable` 为准。
