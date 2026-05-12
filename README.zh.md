# Sci-Integrity Bench

**[English README](README.md)**

本仓库是一套 **仅包含科学家（内层）智能体** 的执行栈：在隔离任务环境中运行内层研究智能体。

## 架构

- **内层科学家智能体**：读取任务、编写代码、作图，并在隔离工作区内产出报告。
- **元入口（meta）**：
  - `meta_benchmark/run_new_scenarios.py`：在 `meta_benchmark/new_scenarios/<scenario_id>/` 下批量运行。
  - `meta_benchmark/run_single_scenario.py`：单场景运行（内部委托给 `run_new_scenarios.py --only <scenario_id>`）。
- **执行核心**：
  - `meta_benchmark/inner_tool.py`：批量调度、工作区拷贝、逐场景运行与磁盘产物。
  - `tier_benchmark/agent_runner.py`：内层科学家智能体循环驱动。
  - `tier_benchmark/unified_system_prompt.py`：共享系统提示构建。

## 仓库结构

- `meta_benchmark/new_scenarios/`：可运行场景（目录名即 `scenario_id`；各目录含 `task_info.json` 与 `data/`）。聚合可读索引 `TASK_INFO_REGISTER.md` 及维护用生成脚本位于该目录下，已列入 `.gitignore`；若使用请在本地保留。
- `meta_benchmark/_authoring_private/`：作者侧材料（不会复制进内层工作区；复制场景树时排除 `target_study/` 等前缀）。审稿用清单：`meta_benchmark/_authoring_private/new_scenario_checklists/<scenario_id>.json`。
- `docs/`：文档（`docs/` 下不再单独维护任务登记表；请使用上文路径）。
- `meta_runs/`：默认运行输出根目录（在 `.gitignore` 中；默认不纳入版本库）。
- `_deprecated/`：归档脚本（整棵目录已 gitignore；若仍使用请在本地保留克隆）。

## 环境准备

1. **安装依赖**

```bash
pip install -r requirements.txt
```

2. **环境变量**

- 将 `.env.example` 复制为 `.env`，并按所用厂商填写对应块。
- 支持的 **命名块**（见 `llm_env.py`）：`DEEPSEEK_*`、`GLM_*`、`CLAUDE_*`（OpenAI 兼容网关）、`SILICON_*`、`OPENROUTER_*`。
- **旧版** 单块覆盖：`LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`。

3. **CLI 模型相关参数**

`run_new_scenarios.py` / `run_single_scenario.py` 通过 `add_llm_cli_args` 接受：

- `--provider {deepseek,glm,claude,silicon,openrouter}` — 选用 `.env` 中哪一组凭据（省略 `--model` 时使用该块默认模型）。
- `--model <id>` — 模型 id（如 `deepseek-chat`、`glm-4-flash`，或 OpenRouter 风格 `anthropic/claude-sonnet-4.6`）。
- `--api-key` / `--base-url` — 本次运行覆盖密钥与 base URL。
- `--inner-max-steps` — 智能体步数上限（默认 `50`）。
- `--results-dir` — 运行结果父目录（相对仓库根，默认 `meta_runs`）。
- `--plain-run-dir` — 批次目录命名为 `new_<timestamp>`，而非 `new_<model>_<timestamp>`。
- `--into-existing <path>` — 复用已有批次根（在 `round_001/` 下）；与 `--only` 联用时，按 `scenario_id` 合并更新 `outer_workspace/inner_results_r001.json` 中的行。
- `--soft-system-prompt` — 使用低压/软提示的系统与用户提示（见下文 **软系统提示**）。

## 运行

场景摘要与完整 `task_info.json` 正文：若本地已生成，见 `meta_benchmark/new_scenarios/TASK_INFO_REGISTER.md`（不提交到仓库）。  
作者用清单（不会注入智能体工作区）：`meta_benchmark/_authoring_private/new_scenario_checklists/*.json`。

```bash
# 所有 scenario_id 形如 NN<字母>_ 且字母为 a 的批量（如 01a_、02a_、…）
python meta_benchmark/run_new_scenarios.py --letter a --provider deepseek --model deepseek-chat --results-dir meta_runs

# 显式列表
python meta_benchmark/run_new_scenarios.py --only 01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling --provider glm --model glm-4-flash --results-dir meta_runs

# 单场景
python meta_benchmark/run_single_scenario.py --scenario 09a_NuclearScience_Iodine131DecayAnalysis --provider deepseek --model deepseek-chat --results-dir meta_runs
```

### 软系统提示（无压力模式）

进行 **低压** 运行时，在上述入口上增加 **`--soft-system-prompt`**。内层智能体会切换到 `tier_benchmark/unified_system_prompt.py` 中的消融提示：保留工作区布局与交付物要求，但去掉严格的「执行协议 / 严禁 / 每条回复必须带工具调用 / 不得停止」等措辞，并使用更短的开场用户行。`done` 隔离规则仍然有效。

```bash
# 批量（按字母筛）— 软提示
python meta_benchmark/run_new_scenarios.py --letter a --soft-system-prompt --provider deepseek --model deepseek-chat --results-dir meta_runs

# 显式列表 — 软提示
python meta_benchmark/run_new_scenarios.py --only 01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling --soft-system-prompt --provider glm --model glm-4-flash --results-dir meta_runs

# 单场景 — 软提示（`run_single_scenario.py` 会将标志转发给 `run_new_scenarios.py`）
python meta_benchmark/run_single_scenario.py --scenario 09a_NuclearScience_Iodine131DecayAnalysis --soft-system-prompt --provider deepseek --model deepseek-chat --results-dir meta_runs
```

批次元数据会在 `meta_summary.json` 的 `soft_system_prompt` 字段中记录该开关。

## 输出目录结构

运行结果默认在 `meta_runs/`（或 `--results-dir` 指定路径）。每个批次会生成类似 `new_<model>_<timestamp>/`（若使用 `--plain-run-dir` 则为 `new_<timestamp>/`）的目录：

- `round_001/outer_workspace/inner_results_r001.json` — 该批次各场景结果汇总。
- `round_001/inner_workspaces/round_001/<scenario_id>/`
  - `trace.json`
  - `run_summary.json`
  - `report/report.md`（及该工作区内智能体写入的其它产物）
- `meta_summary.json` — 批次元数据（在使用 `--into-existing` 且带 `--only` 合并时跳过写入）
