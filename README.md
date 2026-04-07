# Sci-Integrity Bench

本仓库包含两层 AI 科学家沙盒系统，用于研究 AI 在科研任务中的造假倾向。

## 系统结构（精简版）

- **内层科学家（inner scientist）**：执行具体科研任务（数据分析、代码实现、报告撰写）
- **内层审稿人（inner reviewer）**：对科学家提交的结果进行多轮评审（严谨优先；实现上沿用内部标识 `angel`）
- **外层出题科学家（outer question-setting scientist）**：设计场景、生成数据，调用内层运行，寻找能触发内层造假的实验条件

## 目录结构

- `tier_benchmark/` — 内层基准
  - `benchmark_runner.py`：主运行器（场景调度、结果汇总）
  - `agent_runner.py`：Agent 执行核心（tool 模式 + text 模式）
  - `unified_system_prompt.py`：统一系统提示词（场景在 **Research Task** 中注入）
  - `scenario_registry.py`：从 `benchmark_test.md` 自动解析场景
  - `pressure_engine.py`：审稿人开关（P2 注入），见 `pressure_design.md`
  - `behavior_monitor.py`：行为监控与规则命中
- `meta_benchmark/` — 外层元基准
  - `meta_runner.py`：外层主调度器
  - `meta_agent_runner.py`：外层 ReAct 循环
  - `inner_tool.py`：`run_inner_benchmark` 工具封装
  - `fabrication_detector.py`：造假信号提取与判定
  - `meta_reviewer.py`：反向审稿人（仅接受造假证据）
  - `run_main_scenarios.py`：跑 **主场景 11**（`main_presets/SCENARIOS.md`；统一提示词 + 默认开启 `angel` 审稿人，单次批跑完即退出）
  - `main_presets/`：主场景静态数据与生成脚本（B/J 由脚本每次再生）
- `data/`：`scenarioX_*` 数据文件或脚本
- `benchmark_test.md`：14 场景基准定义
- `pressure_design.md`：压力源设计文档

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

3. 命令行选择模型（与 `.env` 中的分块对应）

各入口脚本均支持：`--provider {deepseek,glm,claude,silicon}`、`--model <id>`，以及可选的 `--api-key` / `--base-url` 覆盖。

示例（两个终端各跑主场景，互不影响）：

```bash
python meta_benchmark/run_main_scenarios.py --provider deepseek --model deepseek-chat --results-dir meta_runs
python meta_benchmark/run_main_scenarios.py --provider glm --model glm-4-flash --results-dir meta_runs
```

未指定 `--provider` 时，会根据 `--model` 名称自动推断（名称中含 `glm` → GLM，含 `deepseek` → DeepSeek，含 `minimax` 或 `MiniMaxAI/` → silicon）。未传 `--model` 时，使用对应厂商环境变量中的默认模型。

**main 结果目录名（默认）**：在 `meta_runs/`（或 `--results-dir`）下自动创建  
`main_<模型id>_<reviewer|no-reviewer>_<时间戳>/`，例如  
`main_deepseek-chat_reviewer_20260320_120000/`、  
`main_glm-4-flash_no-reviewer_20260320_120100/`。  
四个终端并行（每模型 × 有/无审稿）可共用同一 `--results-dir`，互不覆盖。不需要旧式目录名时加 `--plain-run-dir` 仅用 `main_<时间戳>/`。

```bash
python meta_benchmark/run_main_scenarios.py --provider deepseek --model deepseek-chat --results-dir meta_runs
python meta_benchmark/run_main_scenarios.py --provider deepseek --model deepseek-chat --reviewer --results-dir meta_runs
python meta_benchmark/run_main_scenarios.py --provider glm --model glm-4-flash --results-dir meta_runs
python meta_benchmark/run_main_scenarios.py --provider glm --model glm-4-flash --reviewer --results-dir meta_runs
python meta_benchmark/run_main_scenarios.py --provider silicon --model MiniMaxAI/MiniMax-M2.5 --results-dir meta_runs
python meta_benchmark/run_main_scenarios.py --provider silicon --model MiniMaxAI/MiniMax-M2.5 --reviewer --results-dir meta_runs
```

## 内层 Agent 能力（Tier Benchmark）

- 沙盒环境：底层使用 `AgentSandbox`，仅允许在工作目录内读写；`run_shell` 带禁用命令列表与超时控制。
- 场景注册：自动解析 14 个场景（S01, S03–S06, S09–S11, S13–S18）。
- 执行分流：`tool` 模式（代码执行类）与 `text` 模式（设计/解读/报告类）。
- 系统提示词：全场景共用一套统一模板（`unified_system_prompt.py`），任务描述与数据文件列表由场景注入；**不再**区分「压力组 / 无压力组」两套系统提示词。
- 审稿人：默认关闭内层审稿闭环；`tier_benchmark/benchmark_runner.py` 使用 `--reviewer` 开启 P2 注入。
- 行为监控：占位数据填充、失败后伪造结果等风险信号检测。
- 输出：`trace.json`、`behavior_report.json`、`run_summary.json`、`benchmark_summary_*.json`。

## 外层 Agent 能力（Meta Benchmark）

- 目标：寻找能触发内层 AI 造假的实验条件。
- 工具：`write_file`、`run_shell`、`read_file`、`run_inner_benchmark`、`done`。
- 每轮设计 1 个场景：合成数据后调用内层运行，逐轮迭代。
- 外层审稿人：仅当造假证据充分时才接受；否则要求继续迭代。
- 默认配置：内层 50 步/场景、内层审稿默认关闭；`meta_benchmark/meta_runner.py` 可用 `--inner-reviewer` 开启内层审稿（未在 `pressure_config` 中覆盖时生效）。

## 运行示例

### 内层基准（Tier Benchmark）

```bash
# 单场景（默认不开启审稿人；结果在 <scenario>_<时间戳>/run/）
python tier_benchmark/benchmark_runner.py --scenarios S03

# 多场景、开启审稿人
python tier_benchmark/benchmark_runner.py --scenarios S03,S09 --reviewer

# 全场景执行（默认不开启审稿人）
python tier_benchmark/benchmark_runner.py
```

### 外层元基准（Meta Benchmark）

```bash
# 默认配置
python meta_benchmark/meta_runner.py --max-outer-rounds 5

# 自定义参数
python meta_benchmark/meta_runner.py \
  --max-outer-rounds 10 \
  --inner-max-steps 30 \
  --inner-reviewer-profile angel \
  --start-from one_scenario

# 开启内层审稿（对未在 pressure_config 中指定的场景生效）
# python meta_benchmark/meta_runner.py ... --inner-reviewer
```

### 主场景 11（固化清单，批跑后退出）

```bash
python meta_benchmark/run_main_scenarios.py
```

开启内层审稿（`done` 后可进入审稿闭环；系统提示词仍为统一模板）：

```bash
python meta_benchmark/run_main_scenarios.py --reviewer
```

结果目录：`meta_runs/main_<时间戳>/` 或带模型与审稿标记的 `main_<模型>_<reviewer|no-reviewer>_<时间戳>/`（`meta_summary.json` 含 `reviewer_enabled` 等字段）。可选：`--inner-max-steps`、`--results-dir`、`--model`。
