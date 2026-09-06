# pilotfish-codex

> Codex 原生的 orchestration layer，根据需求的明确程度与风险，选择合适的
> 第一步：直接执行、探索后规划，或共同澄清。

[English](../README.md) · [繁體中文](./README.zh-TW.md)

Pilotfish-Codex 是受
[Pilotfish](https://github.com/Nanako0129/pilotfish) 启发的独立 Codex CLI
版本。它整合 typed agent roles、明确的 approval boundaries、adaptive intent
routing，以及使用 fresh context 的 outcome verification。

![自适应意图路由：需求、模式、checkpoint 与实验结果](./assets/adaptive-routing-overview-zh-CN.svg)

## 项目做什么

第一步取决于用户的确定程度、变更规模，以及判断错误的成本：

| 需求情况 | 初始模式 | 第一个动作 |
| --- | --- | --- |
| 明确且范围固定 | `execute` | 确认目标与 approval，再采取最小的直接动作。 |
| 范围广或影响高 | `explore_then_plan` | 先确认边界、整理风险，再提出可逆的切片。 |
| 还没有明确边界的想法 | `co_discover` | 提出聚焦问题，定义最小可行的实验。 |

Policy 同时设置 grounding floor，避免资料不足时乱猜；设置 stopping
ceiling，避免分析无限扩张；并使用 `direction_checkpoint` 判断应该继续、转向、
回滚，或向用户补问。

## 从意图到 role

Intent routing 决定交互形状；原本 Pilotfish 的 role system 再把工作分配给
各自边界明确的角色。一个需求不需要经过全部 role。

| 路径 | 常见 role path | 作用 |
| --- | --- | --- |
| `execute` | `executor` 或 `mech-executor` → approval gate → 有风险时再 `verifier` | 实现明确且范围固定的结果，并在 authority gate 前停下。 |
| `explore_then_plan` | `scout` → Plan → 需要 review 时 `plan-verifier` → `executor` 或 `mech-executor` → `verifier` | 先确认边界、审查切片，再实现与验证。 |
| `co_discover` | Root session + 有界的 `scout` → `execute` 或 `explore_then_plan` | 把想法整理成稳定的问题、目标、MVP 与 acceptance boundary。 |
| Security-sensitive work | `security-reviewer` → approved Plan → `security-executor` → `verifier` | 将 security evidence 与 implementation 保持在不同 capability boundary。 |

当前安装的七个 role：

| Role | 职责 |
| --- | --- |
| `scout` | Read-only repository reconnaissance。 |
| `plan-verifier` | 在 approval 前挑战 material Plan。 |
| `executor` | 需要 engineering judgment 的有界实现。 |
| `mech-executor` | 已完整规格化的 mechanical implementation。 |
| `security-reviewer` | approval 前的 read-only security evidence。 |
| `security-executor` | 已批准的 security-sensitive implementation。 |
| `verifier` | 使用 fresh context 验证 outcome 或 direction checkpoint。 |

Root session 负责 routing、Plan synthesis、approval decision、integration 与
finding disposition。完整的 delegation 与 verification 规则请查看
[docs/design.md](./design.md)。

## 为什么这样拆 role

这些 role 将直接执行与高不确定性的 review 分开。v6 benchmark 使用固定的
artifact task 作为 native-rollout proxy：

<img src="./assets/v6-weighted-tokens-zh-CN.svg" alt="每组 12 次试验的加权 token 使用量" width="720">

<img src="./assets/v6-equivalent-cost-zh-CN.svg" alt="每组 12 次试验的等效成本" width="720">

<img src="./assets/v6-median-wall-time-zh-CN.svg" alt="每个候选者的中位 wall time" width="720">

因此，routine 的 `executor`、`mech-executor` 与 verification 工作使用 Luna；
较窄的 `plan-verifier` 与 security review 使用 Sol，让较高成本换取独立的
高 effort 判断；Terra 不设置 active tier。这是 routing decision，不是通用的
intelligence ranking。完整 benchmark 与 bar charts 请查看
[usage-routing benchmark](./benchmarks/usage-routing-v1/README.md)。

## 实验效果

正式 live cohort 使用三个代表性场景，共 60 组案例；每组各执行一次 route
call 与 checkpoint call，使用可解析版本的 Codex CLI；实际版本会记录在
receipt，native contract 由 runtime evidence 验证。

| 指标 | 结果 | 解读 |
| --- | ---: | --- |
| 初始模式 routing | 60 / 60（100.0%） | 三种交互模式都选择正确。 |
| 必要 approval boundary | 60 / 60（100.0%） | 没有漏掉必要的 approval gate。 |
| Direction checkpoint | 59 / 60（98.3%） | 几乎每次都选择正确的下一步方向。 |
| Strict full route contract | 48 / 60（80.0%） | First move 与 grounding 的合并主张尚未达标。 |

这些结果支持较窄的“模式选择、approval 与 checkpoint”主张，不代表每个
response 都完美。Strict misses 与完整分析保留在
[实验结果](./specs/adaptive-intent-routing/EXPERIMENT-RESULTS.md) 中追踪。

## 可选的 root model

全新安装默认使用 Luna medium，已有的模型和 effort 设置会保留。
如果重视响应速度且能接受更高成本，可以在单次 session 中选择 Astra low。
需要 Codex CLI `>=0.153.0` 和 Astra 访问权限；本次实测使用 CLI `0.153.3`。

```bash
codex -m gpt-6-astra -c 'model_reasoning_effort="low"'
```

具名角色的模型绑定不变，Plan mode 仍使用独立的
`plan_mode_reasoning_effort` 设置。
[实测报告](./benchmarks/astra-root-smoke/README.md) 每组只有一个小型 bug
任务，基线是个人 Sol 配置；没有比较上游的 Luna 主模型默认配置，也没有证明
可以节省订阅额度。

## 快速安装

要求：可解析版本的 Codex CLI、Python `3.11+`、Bash，以及本地 checkout。

先执行 dry-run。它只会规划变更，不会写入 Codex home：

```bash
bash install/install.sh --dry-run --codex-home "$ACTIVE_CODEX_HOME"
```

确认要写入的路径并批准 home write 后，再执行：

```bash
bash install/install.sh --codex-home "$ACTIVE_CODEX_HOME"
```

在原生 Windows 上，请从 PowerShell 使用 Python entrypoint，因为
`install/install.sh` 是 Bash wrapper：

```powershell
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME ".codex" }
py -3 install/install.py --dry-run --codex-home $codexHome
py -3 install/install.py --codex-home $codexHome
```

Installer 会加入 native seven-role manifest 与 Pilotfish routing hook。安装后
请在新的交互式 Codex session 中 trust 这个 hook。

Remote installation 必须在 script URL 与 archive ref 使用同一个 release tag
或完整 commit SHA。不要从可变动的 `main` 安装到真实 Codex home。

完整的 approval、migration、backup、recovery 与 trust 步骤请查看
[INSTALL.md](../INSTALL.md)、[install/AGENT-INSTALL.md](../install/AGENT-INSTALL.md)
以及可复用的 [INSTALL_PROMPT.md](../INSTALL_PROMPT.md)。

## 文档导航

| 主题 | 文档 |
| --- | --- |
| Design 与 policy 边界 | [docs/design.md](./design.md) |
| Adaptive routing 设计 | [EXPERIMENT.md](./specs/adaptive-intent-routing/EXPERIMENT.md) |
| Adaptive routing 结果 | [EXPERIMENT-RESULTS.md](./specs/adaptive-intent-routing/EXPERIMENT-RESULTS.md) |
| Live experiment protocol | [LIVE-EXPERIMENT.md](./specs/adaptive-intent-routing/LIVE-EXPERIMENT.md) |
| Usage-routing benchmark | [benchmark README](./benchmarks/usage-routing-v1/README.md) |
| Native verification | [verification README](./verification/README.md) |

## 本地验证

```bash
bun install --frozen-lockfile
bun run lint:md
python3 -m unittest discover -s tests -v
```

## License

MIT。保留原 Pilotfish 的 attribution 与 permission notice。
