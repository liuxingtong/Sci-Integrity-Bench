# AI Scientist 审题人登记表（说明）

正式登记表为 Excel 文件：**`docs/AI_scientist_审题人登记表.xlsx`**

## 结构

- **每个模型一个工作表（sheet）**（不是每个 `run_id` 一张）。同一模型在 `meta_runs` 里的多批次结果会聚合到同一张表中。  
  Excel 对工作表名最长 **31 个字符**，超长时会自动截断；模型标识写在每个 sheet 的 **`B1`**。
- **每个 sheet 固定 33 题（abc 套题）**，来自全局场景清单；这样各模型表结构一致、可横向对比。  
- **场景顺序（同一题号 abc 紧挨）**：先题号 **01→11**，同一题号内再 **a→b→c**。即 `01a, 01b, 01c, 02a, 02b, 02c, …`。为便于区分，**a/b/c** 行使用浅色底纹（可打印时仍清晰）。
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

脚本会扫描 `meta_runs/<run_id>/round_001/inner_workspaces/round_001/` 下的子目录，按模型聚合并生成 sheet，同时统一场景行顺序，**覆盖生成** `docs/AI_scientist_审题人登记表.xlsx`。若 sheet 已手工填写，请先备份再运行。

## 与审查文件的关系

- 登记表的「状态」只表示**协作与确认进度**；**审查结论**仍以 `meta_runs/<run_id>/human_reviews/<scenario_id>.md` 中 `machine_readable` 为准。
