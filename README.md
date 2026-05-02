# Sci-Integrity Bench

本仓库提供 **内层 AI 科学家沙盒**（科研任务执行 + 可选审稿），用于研究 AI 在科研任务中的行为与风险。

## 系统结构（精简版）

- **科学家 Agent（inner）**：执行具体科研任务（数据分析、代码实现、报告撰写）
- **内层审稿人（可选，P2）**：对 `done()` 提交进行多轮评审（严谨优先；内部标识 `angel`）；默认关闭，CLI 用 `--reviewer` 等开启

## 目录结构

- `tier_benchmark/` — Tier 基准（单仓库 14 场景）
  - `benchmark_runner.py`：主运行器（场景调度、结果汇总）
  - `agent_runner.py`：Agent 执行核心（tool 模式 + text 模式）
  - `unified_system_prompt.py`：统一系统提示词（场景在 **Research Task** 中注入）
  - `scenario_registry.py`：从 `benchmark_test.md` 自动解析场景
  - `pressure_engine.py`：审稿人开关（P2 注入），见 `pressure_design.md`
  - `behavior_monitor.py`：行为监控与规则命中
- `meta_benchmark/` — 基于 **`new_scenarios/`** 的批跑与工具封装（无外层红队调度）
  - `inner_tool.py`：`run_inner_benchmark`（多场景隔离工作区）
  - `fabrication_detector.py`：造假信号提取与粗判
  - `run_new_scenarios.py`：**当前主入口**，按目录名批量运行 `meta_benchmark/new_scenarios/<scenario_id>/`（每题含 `task_info.json` 与数据）
  - `run_single_scenario.py`：单题试跑，内部等价于 `run_new_scenarios.py --only <scenario_id>`
  - `new_scenarios/`：共 **33** 道可运行题目（子目录名即 `scenario_id`）
  - `_authoring_private/`：出题/评阅用（含陷阱方法论、`new_scenario_checklists/*.json`），**不**随内层工作区复制给 Agent
- `docs/`：人类可读文档（如 `TASK_INFO_REGISTER.md` 与各题 `task_info` 汇总、`AI_scientist_审查SOP.md` 等）
- `data/`：`scenarioX_*` 等数据文件或脚本
- `benchmark_test.md`：14 场景 Tier 基准定义
- `pressure_design.md`：压力源设计文档
- `_deprecated/`（可选，**已写入 `.gitignore`**）：本地存放已弃用脚本或旧副本，不参与版本控制

## 双盲投稿与发布材料

- 发布范围：`docs/RELEASE_SCOPE.md`
- 双盲打包清单：`docs/ANONYMIZED_SUBMISSION.md`
- 数据卡与格式：`docs/DATASET_DATASHEET.md`、`docs/DATASET_FORMAT.md`
- 人工审查与评测：`docs/AI_scientist_审查SOP.md`、`docs/EVALUATION_POLICY.md`
- 论文对齐：`docs/PAPER_ALIGNMENT.md`
- 版本与校验：`CHANGELOG.md`、`checksums/sha256sums.txt`

## 运行前准备

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 配置环境变量

- 复制 `.env.example` 为 `.env`
- **推荐（双终端并行）**：在 `.env` 中同时配置 `DEEPSEEK_API_KEY` / `DEEPSEEK_BASE_URL` / `DEEPSEEK_MODEL` 与 `GLM_API_KEY` / `GLM_BASE_URL` / `GLM_MODEL`
- **硅基流动（MiniMax 等）**：`SILICON_API_KEY`、`SILICON_BASE_URL`（可写 `https://api.siliconflow.cn`，程序会自动补 `/v1`）、`SILICON_MODEL`（如 `MiniMaxAI/MiniMax-M2.5`）
- **兼容**：仍可使用单一的 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`

3. 命令行选择模型

各入口脚本均支持：`--provider {deepseek,glm,claude,silicon}`、`--model <id>`，以及可选的 `--api-key` / `--base-url` 覆盖。

未指定 `--provider` 时，会根据 `--model` 名称自动推断（名称中含 `glm` → GLM，含 `deepseek` → DeepSeek，含 `minimax` 或 `MiniMaxAI/` → silicon）。未传 `--model` 时，使用对应厂商环境变量中的默认模型。

## Meta 批跑（`meta_benchmark/new_scenarios`，当前题目集）

- **题目清单与简介**：见 `docs/TASK_INFO_REGISTER.md`（与 `meta_benchmark/new_scenarios/` 下 33 个目录一致）。
- **作者侧陷阱检核**：`meta_benchmark/_authoring_private/new_scenario_checklists/<scenario_id>.json`（与目录名同名）。

默认按「题号第二位字母」筛选：例如 `--letter a` 只跑 `01a_*`、`02a_*`、…；`--letter b` 跑 `*b_*`。也可用 `--only` 指定逗号分隔的完整目录名。

```bash
# 跑全部 01a、02a、…（第二位为 a 的目录）
python meta_benchmark/run_new_scenarios.py --letter a --provider deepseek --model deepseek-chat --results-dir meta_runs

# 只跑指定几题
python meta_benchmark/run_new_scenarios.py --only 01a_SymbolicPatternReasoning_BenchmarkSelection,02a_SymbolicPatternReasoning_LabelNoiseCeiling --provider glm --model glm-4-flash --results-dir meta_runs

# 开启内层审稿（P2）
python meta_benchmark/run_new_scenarios.py --letter a --reviewer --provider deepseek --model deepseek-chat --results-dir meta_runs
```

单题（等价于 `--only` 一题）：

```bash
python meta_benchmark/run_single_scenario.py --scenario 09a_NuclearScience_Iodine131DecayAnalysis --provider deepseek --model deepseek-chat --results-dir meta_runs
```

**结果目录（默认）**：在 `meta_runs/`（或 `--results-dir`）下生成  
`new_<模型片段>_<reviewer|no-reviewer>_<时间戳>/`；若加 `--plain-run-dir` 则为 `new_<时间戳>/`。批次元数据见该目录下 `meta_summary.json`（含 `scenario_order`、`author_checklists_dir` 等）。

## 内层 Agent 能力（Tier Benchmark）

- 沙盒环境：底层使用 `AgentSandbox`，仅允许在工作目录内读写；`run_shell` 带禁用命令列表与超时控制。
- 场景注册：自动解析 14 个场景（S01, S03–S06, S09–S11, S13–S18）。
- 执行分流：`tool` 模式（代码执行类）与 `text` 模式（设计/解读/报告类）。
- 系统提示词：全场景共用一套统一模板（`unified_system_prompt.py`），任务描述与数据文件列表由场景注入。
- 审稿人：默认关闭内层审稿闭环；`tier_benchmark/benchmark_runner.py` 使用 `--reviewer` 开启 P2 注入。
- 行为监控：占位数据填充、失败后伪造结果等风险信号检测。
- 输出：`trace.json`、`behavior_report.json`、`run_summary.json`、`benchmark_summary_*.json`。

## 运行示例（Tier）

```bash
# 单场景（默认不开启审稿人；结果在 <scenario>_<时间戳>/run/）
python tier_benchmark/benchmark_runner.py --scenarios S03

# 多场景、开启审稿人
python tier_benchmark/benchmark_runner.py --scenarios S03,S09 --reviewer

# 全场景执行（默认不开启审稿人）
python tier_benchmark/benchmark_runner.py
```
