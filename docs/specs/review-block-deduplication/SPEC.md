---
id: spec-review-block-deduplication
title: Codex general-mode decision checkpoints and review recovery
status: in_progress
created: 2026-08-10
updated: 2026-08-10
author: Miyago
priority: high
tags: [codex, decision-checkpoint, review, circuit-breaker, recovery]
---

## Goal

建立 Codex 一般模式的例外型 decision checkpoint：Codex 預設自行判斷並繼續
可安全執行的工作，只有在 blocker、探索分歧或權限／安全邊界會改變結果時，才
像 Plan mode 一樣提出少量選項並等待使用者選擇。同時修正 review-service
circuit breaker 在同一個 blocker 跨 turn 持續存在時的重複阻塞行為。

本 spec 的 runtime target 是 Codex CLI／App 及其原生 `AGENTS.md`、Plugin、
hooks、roles 與 interactive question 能力；Claude Code、OpenCode、Grok Build
等其他 harness 不在本 spec 的相容性承諾內。

## Release boundary

### Current release

本次處理 Codex 一般模式的 autonomy／checkpoint 邊界，以及 blocker 的跨 turn
去重與死循環：同一個 blocker 只警告一次，後續維持 blocked/waiting state；
正常且可逆的判斷由 Codex 自行完成，不把每個歧義升級成使用者批准。先以最小
可驗證切片完成，確保不破壞既有 mandatory review gate。

### Next release

一般模式 decision checkpoint 保留在本 spec，但明確延後到下一版本。task
ledger、runnable-first scheduler，以及以 task 為單位的 sibling isolation
屬於目前版本的執行規則；本次新增水平並行邊界，仍受 bounded concurrency、
dependency 與 write-ownership 限制。

## Problem

目前 hook 的 marker 以單一 turn 為生命週期。新的 `UserPromptSubmit` 會重新
建立 marker 並將 `attempted` 設回 `false`，所以同一個未解決的 review blocker
跨 turn 後可能再次觸發完全相同的 `BLOCK_OUTPUT`。實際效果是 agent 被自己
卡在重複提醒迴圈，例如反覆要求重開機，而沒有繼續其他可做的工作。

## Requirements

- 同一個穩定 blocker 只發出一次人類可見的阻塞警告。
- 第一次警告後進入 `WAITING_FOR_REVIEW`，不得因新 turn 或重複 Stop event
  重設 retry 狀態。
- 等待狀態不得重複輸出相同句子、要求相同動作或自行擴大阻塞範圍。
- 同一個 prompt 若包含複數任務，必須先拆成互相可識別的 task units，並以
  task 為 blocker、receipt、完成與 recovery 的最小狀態單位。
- 某一 task blocked 時，不得鎖定同一 prompt 中仍可安全執行的 sibling tasks。
- 只要仍有 runnable task，阻塞提醒應被抑制或降為非中斷的狀態紀錄。
- 沒有 dependency path 且沒有 write-ownership/resource conflict 的 runnable
  tasks 應水平並行執行，受 bounded concurrency 限制。
- 有 dependency path 的 tasks 必須等待 predecessor；共用 mutable resource 或
  exclusive file scope 的 tasks 必須序列化。
- 所有 runnable tasks 完成且只剩 blocked tasks 時，才發出一次彙總提醒並中斷
  當前行為，等待人類確認或排除 blocker。
- goal 的整體狀態在仍有 blocked task 時不得標記為完成；應保留 blocked 狀態
  與每個 task 的獨立結果。
- Codex 一般模式預設自行處理低風險、可逆、scope 明確且可由現有證據判斷的
  選擇，不得因每個小歧義要求使用者批准。
- 當 task 拆分、blocker 處理、探索方向、風險、權限或驗收條件會改變結果時，
  必須能提出結構化 decision checkpoint，讓使用者選擇後再繼續受影響的 task。
- decision checkpoint 應提供少量、互斥、可理解的選項與推薦預設，不得把
  未決的產品或安全選擇藏在自由文字推測裡。
- 一般模式每次 checkpoint 只問一個高層方向問題；不得模仿 Plan mode 展開
  多題細節問卷，細節應在選定方向恢復後於新的 material boundary 再詢問。
- 若問題只影響單一 blocked task，checkpoint 不得要求使用者重新確認已完成
  或可獨立執行的 sibling tasks。
- 有效的 `plan-verifier` / `verifier` receipt、明確的人為解除，或任務識別
  已變更時，才可以清除或重新建立 blocker state。
- 既有 mandatory review、approval、permission、security、external、release
  與 irreversible 邊界不得因去重而弱化。
- marker state 必須維持現有 bounded、fail-closed、integrity-checking 行為。
- 不保存完整 prompt 或敏感內容；若需要跨 turn 識別，僅保存穩定 fingerprint。

## Decisions

1. 將 goal 拆成可獨立追蹤的 task units；每個 task 至少保存穩定 identity、
   status、dependencies、blocker fingerprint 與 completion evidence。
2. task lifecycle 從單次 `attempted` 布林值提升為明確 state：
   `PENDING` → `RUNNING` → `DONE`，或 `RUNNING` → `BLOCKED` → `CLEARED`。
3. 去重範圍以 task/blocker fingerprint 為準，不以整個 session 無期限封鎖
   所有後續工作。
4. `BLOCK_OUTPUT` 僅允許在該 task 第一次進入 `BLOCKED` 時發出一次；後續
   `BLOCKED` state 不得重新發出同一個阻塞輸出。
5. scheduler 必須優先選擇沒有 blocker 且 dependencies 已滿足的 runnable task。
   某 task blocked 不得阻止 sibling task 完成。
6. 只要仍有 runnable task，blocker 僅保留在狀態資料中，最多產生非中斷提醒。
   當 runnable task 清空且仍存在 blocked task 時，才發出一次彙總警告並停止，
   等待人類確認或排除。
7. 人為介入是合法 recovery path：使用者可以排除 blocker、提供 review
   receipt，或明確要求解除等待；解除後才允許重新評估該 task。
8. 若 hook 無法可靠判斷 task identity、marker integrity 或 transcript evidence，
   維持 fail-closed 的安全邊界，但輸出必須是一次性、可恢復的狀態訊號，
   不得形成無限重試。
9. 一般模式的 decision checkpoint 是互動層契約，類似 Plan mode 的選項卡，
   但不是每一步的 approval gate。Codex 預設自行決定；checkpoint 只負責把
   會改變結果、權限、風險或驗收的 decision 顯式化，不取代既有 approval、
   permission 或安全 gate。
10. Decision checkpoint 至少支援：task 拆分確認、blocked task 的處置、是否
    先完成其他 runnable tasks，以及完成後是否暫停等待人類介入。
11. 原生 card mode 是預設問答 surface；獨立的 MCP elicitation bridge 只能作為
    optional transport，不能成為 Pilotfish core dependency，也不能改變既有
    checkpoint schema、scope 或 approval boundary。
12. 一般模式 checkpoint 固定為單題高層方向選擇；後續細節不在同一張 card
    內展開，避免把一般模式變成 Plan mode 問卷。

## Codex general-mode decision checkpoint

一般模式的 checkpoint 不是把整個流程切換成完整 Plan mode，而是在需要決策
的單一邊界暫停，等待使用者回覆。預設由 Codex 自己選擇合理、低風險且可回復
的方案；只有真正會改變結果、權限、風險或驗收的 decision 才能觸發 checkpoint。
每次最多提出三個問題；沒有這類 decision 時直接繼續執行。

### Autonomous default

- scope 明確、可逆、低風險且不涉及 external、credential、release 或 destructive
  operation 時，Codex 直接採用合理預設並記錄判斷。
- 低成本探索可以直接執行；只有探索結果形成會影響實作、產品行為、驗收或
  scope 的分歧時，才提出選項。
- blocker 若不影響其他 runnable tasks，Codex 先完成可安全執行的 sibling tasks；
  只有沒有可執行工作，或 blocker 的處置會改變結果時，才中斷並詢問。
- checkpoint 是例外型決策機制，不是逐步人工批准流程。

建議的結構化內容：

```text
Decision checkpoint
Scope: task decomposition and blocker handling
Current interpretation: WSL update needs reboot; PowerShell and VS Code can continue.
Recommended: finish runnable tasks first

1. Finish PowerShell and VS Code, then stop for WSL reboot
2. Stop all tasks now and wait for reboot
3. Mark WSL blocked and continue only with explicitly approved local tasks

Resume point: after the selected option is confirmed
```

規則：

- checkpoint 必須說明目前 interpretation、影響範圍、推薦選項、排除範圍與
  resume point。
- 選項必須互斥；使用者選項不明確時保持等待，不得猜測成批准。
- 一般模式若沒有原生互動式 question tool，使用相同 schema 的文字 decision
  card；不能假裝已取得選擇。
- 使用者確認只授權該 checkpoint 內的 task scope，不會自動批准 credentials、
  external writes、release、destructive 或 irreversible operations。
- 使用者要求繼續時，回覆必須保留 task ledger、blocked task 與下一個最小
  resume point，避免下一輪重新詢問同一題。

## Tasks

- [x] T1 — 定義跨 turn blocker/task fingerprint 與 marker schema migration
  （current release）。
- [x] T2 — 定義 prompt-to-task decomposition、task dependencies 與 goal aggregate
  status；blocked task 不得使 sibling task 自動 blocked。
- [x] T3 — 實作 task-level state、`PENDING`、`RUNNING`、`DONE`、`BLOCKED`、
  `CLEARED` 狀態轉換與人為解除入口。
- [x] T4 — 實作 runnable-first scheduling，以及「只剩 blocked tasks 才中斷」
  的彙總提醒策略。
- [x] T5 — 定義一般模式 decision checkpoint 的觸發條件、選項 schema、推薦
  預設與使用者回覆的 resume contract。
- [x] T6 — 新增跨 turn duplicate-warning regression tests（current release）。
- [x] T7 — 新增複數 task isolation、sibling completion、blocked-only summary、
  receipt-clears、human-clears 與 malformed-state fail-closed tests。
- [x] T8 — 新增一般模式 decision checkpoint 的選項、確認、拒絕、模糊回覆與
  session resume tests；確認它不會越權批准外部或不可逆操作。
- [ ] T9 — 在 macOS、Linux、Windows 驗證 hook launch、marker handling、path
  scanner 與既有 review gate parity。
- [x] T11 — 將一般模式 checkpoint 收斂為 autonomous default 加上例外型觸發，
  並確認低風險歧義不會被升級成使用者批准。
- [x] T12 — 新增 autonomy regression tests：Codex 自行採用合理預設、探索分歧
  才提問、blocker 不影響 sibling tasks，以及權限／安全邊界仍會停下。
- [x] T13 — 定義 optional MCP elicitation adapter 邊界：原生 card 預設、MCP
  可選引用、unsupported/cancel/timeout/invalid 時回退文字或原生 card。
- [x] T14 — 將一般模式問答收斂為單一高層方向題，並禁止同一 checkpoint
  展開多題細節問卷。
- [x] T10 — 更新 `CHANGELOG.md`、安裝說明與 recovery 操作文件。

## Files

- `hooks/pilotfish_autoroute_gate.py` — blocker state、fingerprint、marker lifecycle。
- `tests/test_autoroute_hook.py` — 跨 turn、去重、解除與無關任務測試。
- `templates/agents-md.orchestration.md` — task decomposition、goal aggregate
  status、blocked-only interruption 與 Codex 一般模式 decision checkpoint 契約。
- `install/install.py` — 如 marker schema 或 recovery migration 需要安裝器支援。
- `INSTALL.md` — 新增 blocker recovery 與人工解除說明。
- `CHANGELOG.md` — 記錄修正與相容性影響。
- `../../../../choicebridge/docs/specs/elicitation-bridge/SPEC.md` — 獨立 MCP
  extension 的產品與 protocol spec；Pilotfish 僅作 optional consumer。

## Acceptance

- 同一 session、同一 blocker 連續觸發多個 turn 時，`BLOCK_OUTPUT` 恰好出現
  一次；後續不再重複相同警告。
- 一個 prompt 拆成 WSL、PowerShell、VS Code 三個 tasks 時，WSL 的 reboot
  blocker 只標記 WSL；PowerShell 與 VS Code 可完成的部分仍會完成。
- 只要 PowerShell 或 VS Code 尚未完成，WSL blocker 不會中斷整體流程；最多
  以非中斷狀態保留提醒。
- PowerShell 與 VS Code 完成後若只剩 WSL blocked，才會輸出一次包含 blocker
  與下一步的人類可操作彙總，並停止等待確認。
- goal aggregate status 在 WSL 尚未解除時為 `BLOCKED`，不得誤報 `DONE`。
- 當 task 拆分或 blocker 處置會改變結果時，一般模式會先提出結構化選項，
  使用者確認後才繼續受影響的 task。
- 使用者選擇「先完成其他 runnable tasks」時，Codex 不得因單一 blocker 中斷
  sibling tasks；選擇「立即停止」時才進入人類介入等待。
- Codex 對低風險且可逆的歧義會自行採用合理預設，不會把每個小選擇交回使用者。
- 一般模式 decision checkpoint 的拒絕、模糊或逾時回覆不得被當成批准；受影響
  task 必須保持未完成或 `BLOCKED`。
- 既有 review receipt 到達後，下一次檢查會清除等待狀態並恢復正常流程。
- 人為解除後，原 blocker 不再阻塞；新的獨立 blocker 仍可正常觸發一次警告。
- 無關 read-only、local preparation 與其他非同一 task 的工作可以繼續。
- 既有 mandatory review negative tests 全數保持通過，不能因去重而允許未審查
  的 external、release、credential、secret 或 irreversible write。
- 重複 prompt、重複 Stop event、process restart、malformed marker、symlink
  marker、跨平台 path handling 都有 regression coverage。
- 既有測試與新增測試全部通過；至少完成三平台 hook self-test 與 config/role
  validation。

## Rollback

若新 state schema 或 recovery path 造成安全邊界退化，回退到上一個已驗證的
marker schema 與一次性 block 行為，保留 mandatory review gate；不得回退成
無上限重複輸出的 retry loop。

## Related

- `docs/specs/intent-aware-review-routing-1-6-0/SPEC.md`
- `docs/specs/intent-aware-review-routing-1-6-0/PROGRESS.md`

## Notes

前三項目前以 orchestration policy 的 task ledger 契約落地，沒有新增外部持久化
task database；ledger 由 main session 維護，避免把 prompt-level blocker 再次
擴大成 session-wide lock。Decision checkpoint 已以 Codex Skill policy 與純驗證
模組落地；本次後續收斂為 autonomous default 加上例外型提問。原生 card 是預設
surface，MCP elicitation bridge 另案維護，僅在可用時作 structured transport。
T9 的三平台 hook parity 仍是獨立驗證 slice；其他 harness 不屬於本 spec 的
runtime target。
