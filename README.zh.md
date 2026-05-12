# Sci-Integrity Bench

**[English README](README.md)**

## 概述

AI 科学家系统正被大规模用于全自动化研究，但其学术诚信从未得到系统性评估。本仓库与论文 [**SciIntegrity-Bench: A Benchmark for Evaluating Academic Integrity in AI Scientist Systems**](http://arxiv.org/html/2605.10246) 配套，该工作提出了首个专门面向这一问题的基准测试。

基准的核心设计理念是**两难式评测**：每个场景都被构造为「诚实承认任务无法完成」才是唯一正确答案，而若强行产出结果则必然涉及学术不当行为。评测涵盖 **11 类不当行为陷阱**（包括数据捏造、违反约束条件、因果混淆等）和 **33 个两难场景**，横跨多个科学领域。

![两难式评测示意图：任务完成压力与诚实拒答](images/dilemma.png)

在 **7 款前沿大模型**（共 231 次运行）上的评测显示，总体诚信问题率达 **34.2%**——约每三个任务就有一个引发捏造或误报，且无任何模型实现零失败。在数据缺失场景中，7 个模型无一例外地生成了合成数据，而非承认任务不可行。消融实验进一步表明，去除完成压力后，未披露的捏造行为从 20.6% 降至 3.2%，但底层合成率未变——揭示出一种独立于提示设计之外的内在「完成偏向」。

本仓库提供论文评测所使用的智能体执行环境：研究智能体在隔离的工作区中逐场景运行，可用于复现或扩展基准评测。

## 架构

- **研究智能体**：读取任务、编写代码、作图，并在隔离工作区内产出报告。
- **运行入口**：
  - `meta_benchmark/run_new_scenarios.py`：在 `meta_benchmark/new_scenarios/<scenario_id>/` 下批量运行。
  - `meta_benchmark/run_single_scenario.py`：单场景运行（内部委托给 `run_new_scenarios.py --only <scenario_id>`）。
- **执行核心**：
  - `meta_benchmark/inner_tool.py`：批量调度、工作区复制、逐场景运行与结果落盘。
  - `tier_benchmark/agent_runner.py`：智能体主循环驱动。
  - `tier_benchmark/unified_system_prompt.py`：系统提示生成器。

![智能体架构：提示与压力、Reason–Act–Observe 循环、工具与终止状态](images/agent.png)

## 仓库结构

- `meta_benchmark/new_scenarios/`：可运行场景（目录名即 `scenario_id`；各目录含 `task_info.json` 与 `data/`）。聚合可读索引 `TASK_INFO_REGISTER.md` 及维护用生成脚本位于该目录下，已列入 `.gitignore`；若需使用请在本地保留。
- `meta_benchmark/_authoring_private/`：作者侧材料，不会复制进智能体工作区（复制场景树时排除 `target_study/` 等前缀）。审核清单：`meta_benchmark/_authoring_private/new_scenario_checklists/<scenario_id>.json`。
- `docs/`：文档（`docs/` 下不单独维护任务索引；请使用上文路径）。
- `meta_runs/`：默认运行输出目录（已列入 `.gitignore`，不纳入版本库）。
- `_deprecated/`：归档脚本（整个目录已 gitignore；如仍需使用请在本地保留）。

## 安装配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境变量

- 将 `.env.example` 复制为 `.env`，并按所用服务商填写对应配置块。
- 支持的**命名块**（见 `llm_env.py`）：`DEEPSEEK_*`、`GLM_*`、`CLAUDE_*`（OpenAI 兼容网关）、`SILICON_*`、`OPENROUTER_*`。
- **旧版**单块覆盖：`LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL`。

### 3. CLI 模型参数

`run_new_scenarios.py` / `run_single_scenario.py` 通过 `add_llm_cli_args` 支持以下参数：

- `--provider {deepseek,glm,claude,silicon,openrouter}` — 选用 `.env` 中对应的凭据块（省略 `--model` 时使用该块默认模型）。
- `--model <id>` — 模型 id，如 `deepseek-chat`、`glm-4-flash`，或 OpenRouter 格式 `anthropic/claude-sonnet-4.6`。
- `--api-key` / `--base-url` — 本次运行覆盖密钥与 base URL。
- `--inner-max-steps` — 智能体步数上限（默认 `50`）。
- `--results-dir` — 运行结果父目录（相对仓库根，默认 `meta_runs`）。
- `--plain-run-dir` — 批次目录命名为 `new_<timestamp>`，而非 `new_<model>_<timestamp>`。
- `--into-existing <path>` — 复用已有批次根（在 `round_001/` 下）；与 `--only` 联用时，按 `scenario_id` 合并更新 `outer_workspace/inner_results_r001.json`。
- `--soft-system-prompt` — 使用低压提示（见下文**软系统提示**）。

## 使用说明

场景摘要与完整 `task_info.json` 正文：若本地已生成，见 `meta_benchmark/new_scenarios/TASK_INFO_REGISTER.md`（不提交到仓库）。  
审核清单（不注入智能体工作区）：`meta_benchmark/_authoring_private/new_scenario_checklists/*.json`。

### 运行场景

```bash
# 所有 scenario_id 字母标识为 a 的场景（如 01a_、02a_、…）
python meta_benchmark/run_new_scenarios.py --letter a --provider deepseek --model deepseek-chat --results-dir meta_runs

# 指定场景列表
python meta_benchmark/run_new_scenarios.py --only 01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling --provider glm --model glm-4-flash --results-dir meta_runs

# 单个场景
python meta_benchmark/run_single_scenario.py --scenario 09a_NuclearScience_Iodine131DecayAnalysis --provider deepseek --model deepseek-chat --results-dir meta_runs
```

### 软系统提示

添加 **`--soft-system-prompt`** 可进行低压模式运行：智能体切换到 `tier_benchmark/unified_system_prompt.py` 中的消融提示，保留工作区布局与交付物要求，但去掉「严格执行协议 / 严禁 / 每条回复必须带工具调用 / 不得停止」等强制措辞，并使用更简短的开场提示。`done` 隔离规则仍然有效。

```bash
# 批量（按字母筛）
python meta_benchmark/run_new_scenarios.py --letter a --soft-system-prompt --provider deepseek --model deepseek-chat --results-dir meta_runs

# 指定列表
python meta_benchmark/run_new_scenarios.py --only 01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling --soft-system-prompt --provider glm --model glm-4-flash --results-dir meta_runs

# 单个场景（`run_single_scenario.py` 会将参数转发给 `run_new_scenarios.py`）
python meta_benchmark/run_single_scenario.py --scenario 09a_NuclearScience_Iodine131DecayAnalysis --soft-system-prompt --provider deepseek --model deepseek-chat --results-dir meta_runs
```

批次元数据会在 `meta_summary.json` 的 `soft_system_prompt` 字段中记录该开关状态。

### 输出目录结构

运行结果默认输出到 `meta_runs/`（或 `--results-dir` 指定路径）。每个批次生成类似 `new_<model>_<timestamp>/`（`--plain-run-dir` 时为 `new_<timestamp>/`）的目录：

- `round_001/outer_workspace/inner_results_r001.json` — 该批次各场景结果汇总
- `round_001/inner_workspaces/round_001/<scenario_id>/`
  - `trace.json`
  - `run_summary.json`
  - `report/report.md`（及工作区内智能体写入的其他产物）
- `meta_summary.json` — 批次元数据（使用 `--into-existing` 加 `--only` 合并时跳过写入）

## 贡献与交流

欢迎自然语言处理、机器学习、AI 安全与软件工程等领域的研究者参与讨论和贡献！请通过 Issue 或 Pull Request 提交反馈，有模板时请按模板填写，以便我们及时跟进。

**论文：** [SciIntegrity-Bench (arXiv:2605.10246)](https://arxiv.org/abs/2605.10246)  
**作者：** Zonglin Yang、Xingtong Liu、Xinyan Xu  
**联系方式：** Zonglin Yang（2501111815@stu.pku.edu.cn）

## 引用

若使用本基准或代码仓库，请引用：

```bibtex
@misc{yang2026sciintegritybenchbenchmarkevaluatingacademic,
      title={SciIntegrity-Bench: A Benchmark for Evaluating Academic Integrity in AI Scientist Systems},
      author={Zonglin Yang and Xingtong Liu and Xinyan Xu},
      year={2026},
      eprint={2605.10246},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2605.10246},
}
```
