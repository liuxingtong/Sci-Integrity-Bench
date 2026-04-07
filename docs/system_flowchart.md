# AI Scientist 系统流程图

## 内层 Agent 流程（Inner Benchmark）

```mermaid
flowchart TB
    subgraph Inputs["系统输入"]
        SP[System Prompts<br/>系统提示词]
        S1[Unified template<br/>统一模板 + 工具协议]
        S2[Scenario: Research Task 注入<br/>任务描述 / 数据文件]
        S3[Optional: P2<br/>审稿预注入（启用审稿时）]
    end

    subgraph Agent["Agent 主循环"]
        LLM[LLM 生成]
        Parse[解析 Tool Call]
        Exec[执行工具]
        Result[工具结果]
        Reflect[反馈给 LLM]
    end

    subgraph Tools["可用工具"]
        T1[write_file]
        T2[edit_file]
        T3[read_file]
        T4[run_shell]
        T5[list_files]
        T6[done]
        T7[quit]
    end

    subgraph Reviewer["审稿人 (P2 启用时；默认开启)"]
        FMT[附加准则<br/>reviewer_criteria_extra]
        CNT[内容审查<br/>严谨向审稿]
    end

    subgraph Terminate["终止状态"]
        Done[Done<br/>任务完成]
        Quit[Quit<br/>项目失败]
        Pass[positive_publishable]
        Fail[project_failure]
        Fab[fabrication_detected]
    end

    SP --> S1
    S1 --> S2
    S2 --> S3
    S3 --> LLM

    LLM --> Parse
    Parse --> Exec
    Exec --> Tools
    Tools --> Result
    Result --> Reflect
    Reflect --> LLM

    Exec -->|done 调用| Reviewer
    Reviewer --> FMT
    FMT --> CNT
    CNT -->|通过| Pass
    CNT -->|负面结果| Fail
    CNT -->|造假| Fab
    CNT -->|needs_revision| Reflect

    Pass --> Done
    Fail --> Done
    Fab --> Done

    Exec -->|quit 调用| Quit
    Quit -->|不触发审稿| Terminate
```

## 简化版：默认配置（统一提示词 + 审稿人默认开）

```mermaid
flowchart LR
    subgraph Init["初始化"]
        A[System + Research Task + P2 审稿]
    end

    subgraph Loop["Agent 循环"]
        B[LLM]
        C[执行工具]
        D[结果反馈]
    end

    subgraph Exit["退出"]
        E[done]
        F[quit]
        R[审稿人]
    end

    A --> B
    B --> C
    C --> D
    D --> B

    C -->|完成交付| E
    C -->|无法完成| F

    E --> R
    R --> End1[结束]
    F --> End2[项目失败]
```

> **说明：** 系统提示词为统一模板（`tier_benchmark/unified_system_prompt.py`），情景由 **Research Task** 注入。仅 **P2** 表示审稿人相关注入；`benchmark_runner` 默认不启用审稿，使用 `--reviewer` 开启；未启用 P2 时 `done()` 后不再进入审稿环节。

## 详细版：含审稿人分支（默认 P2 启用）

```mermaid
flowchart TB
    Start([开始]) --> Init[加载 System + Scenario + P2 可选]
    Init --> Loop

    subgraph Loop["ReAct 循环"]
        LLM[LLM 生成 JSON]
        Parse{解析 tool_call}
        Tool[执行工具]
        Feedback[结果反馈]
    end

    Loop --> Parse
    Parse -->|无有效调用| LLM
    Parse -->|有调用| Tool

    Tool -->|write/edit/read/shell/list| Feedback
    Tool -->|done| Reviewer
    Tool -->|quit| QuitEnd[Quit 退出<br/>不触发审稿]

    Feedback --> CheckStep{达到 max_steps?}
    CheckStep -->|否| LLM
    CheckStep -->|是| MaxEnd[MaxSteps 退出]

    subgraph Reviewer["审稿人"]
        R1[_run_reviewer_judge]
        R2{decision}
    end

    Reviewer --> R1
    R1 --> R2
    R2 -->|positive_publishable| Done1[Done]
    R2 -->|project_failure| Done2[Done]
    R2 -->|fabrication_detected| Done3[Done]
    R2 -->|needs_revision| RevMsg[反馈给 Agent]
    RevMsg --> LLM
```

## 工具调用与审稿触发关系

| 工具 | 是否触发审稿 | 说明 |
|------|-------------|------|
| write_file, edit_file, read_file, run_shell, list_files | 否 | 普通工具，结果直接反馈 |
| done | 是（`--reviewer` / P2 启用时） | 请求审稿，审稿人评估后决定通过/打回；未启用 P2 时直接结束 |
| quit | 否 | 直接退出，不触发审稿，表示项目失败 |

## 与参考流程图的差异

1. **审稿触发时机**：当前系统仅在 `done()` 时触发审稿，不是每次工具执行后都做格式/内容审查。
2. **无道德审查**：没有单独的 "Moral Review" 阶段，审稿人的内容审查已包含对造假的判断。
3. **Quit 路径**：Agent 调用 `quit` 时直接退出，不经过审稿。
4. **审稿开关**：实现上仍用 **P2** 标识审稿注入；tier / meta 默认 **启用审稿人**。未启用 P2 时 `done()` 后直接结束，无审稿环节。详见根目录 `pressure_design.md` 与 `README.md`。
