---
id: spec-review-block-deduplication
title: Review blocker deduplication and human recovery
status: in_progress
created: 2026-08-10
updated: 2026-08-10
author: Miyago
priority: high
tags: [hook, review, circuit-breaker, waiting-state, recovery]
---

## Goal

修正 review-service circuit breaker 在同一個 blocker 跨 turn 持續存在時的
重複阻塞行為。必要警告只輸出一次；後續維持可辨識的等待狀態，不得讓 Stop
hook 反覆輸出相同訊息、要求相同動作，或阻止與該 blocker 無關的工作。

## Release boundary

### Current release

本次只處理 blocker 的跨 turn 去重與死循環：同一個 blocker 只警告一次，
後續維持 blocked/waiting state，不重新輸出同一個阻塞訊息。先以最小可驗證
切片完成，確保不破壞既有 mandatory review gate。

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
- Codex 一般模式在 task 拆分、blocker 處理、風險、權限或驗收條件會影響
  結果時，必須能提出結構化 decision checkpoint，讓使用者確認後再繼續。
- decision checkpoint 應提供少量、互斥、可理解的選項與推薦預設，不得把
  未決的產品或安全選擇藏在自由文字推測裡。
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
9. 一般模式的 decision checkpoint 是互動層契約，不等同於 Plan mode，也不
   取代既有 approval、permission 或安全 gate。它只負責把需要使用者選擇的
   decision 顯式化，確認後才繼續受影響的 task。
10. Decision checkpoint 至少支援：task 拆分確認、blocked task 的處置、是否
    先完成其他 runnable tasks，以及完成後是否暫停等待人類介入。

## General-mode decision checkpoint

一般模式的 checkpoint 不是把整個流程切換成完整 Plan mode，而是在需要決策
的單一邊界暫停，等待使用者回覆。每次最多提出三個真正會改變結果、權限、
風險或驗收的問題；沒有這類 decision 時直接繼續執行。

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
- [ ] T5 — 定義一般模式 decision checkpoint 的觸發條件、選項 schema、推薦
  預設與使用者回覆的 resume contract（next release）。
- [x] T6 — 新增跨 turn duplicate-warning regression tests（current release）。
- [x] T7 — 新增複數 task isolation、sibling completion、blocked-only summary、
  receipt-clears、human-clears 與 malformed-state fail-closed tests。
- [ ] T8 — 新增一般模式 decision checkpoint 的選項、確認、拒絕、模糊回覆與
  session resume tests；確認它不會越權批准外部或不可逆操作（next release）。
- [ ] T9 — 在 macOS、Linux、Windows 驗證 hook launch、marker handling、path
  scanner 與既有 review gate parity。
- [ ] T10 — 更新 `CHANGELOG.md`、安裝說明與 recovery 操作文件。

## Files

- `hooks/pilotfish_autoroute_gate.py` — blocker state、fingerprint、marker lifecycle。
- `tests/test_autoroute_hook.py` — 跨 turn、去重、解除與無關任務測試。
- `templates/agents-md.orchestration.md` — task decomposition、goal aggregate
  status、blocked-only interruption 與一般模式 decision checkpoint 契約。
- `install/install.py` — 如 marker schema 或 recovery migration 需要安裝器支援。
- `INSTALL.md` — 新增 blocker recovery 與人工解除說明。
- `CHANGELOG.md` — 記錄修正與相容性影響。

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
擴大成 session-wide lock。一般模式 decision checkpoint 仍是下一版本範圍。
