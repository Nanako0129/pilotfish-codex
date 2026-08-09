# Quality-first cost frontier

## 結論

這次 12-case live adjudicator cohort 在新的價值規則下，通過「成本前緣」但尚未通過「品質明確提升」：

| 指標 | 結果 | 判定 |
| --- | ---: | --- |
| Luna 品質平均分 | 56.08 | 品質基準 |
| Candidate 品質平均分 | 61.46 | 點估計 +5.38 |
| Candidate 對 Luna 品質 CI lower bound | 0.00 | 尚不能宣稱更好 |
| Candidate 估算成本 / 12 cases | `$0.430` | — |
| 純 Sol 成本基準 / 12 cases | `$2.932` | Candidate 較便宜 |
| 純 Terra 成本基準 / 12 cases | `$1.364` | Candidate 較便宜 |

因此目前的結果是：

```text
品質下限通過 AND 比純 Sol 或純 Terra 便宜 => 通過 quality-first cost frontier
品質 CI 明確高於 Luna              => 尚未通過
```

這不是把品質讓給省錢。若 Candidate 的品質低於 Luna，無論多便宜都會 fail closed。

## 成本算法

成本以每個模型在既有 `live-v6-summary.json` 的 recorded equivalent cost ÷ weighted tokens 得到有效單位成本，再乘以本次報告中各 stage 的 weighted tokens：

- 不分歧：Luna primary 成本。
- 分歧：Luna primary + Sol adjudicator 成本。
- 時間獨立列為 routing UX 指標，不進入品質成本判定。

完整機器可讀結果在 [quality-first-cost-frontier.json](quality-first-cost-frontier.json)。

## 限制

純 Sol/Terra 成本來自既有 `live-v6` reference cohort，不是同一批 12 個 Plan 的 paired quality run；因此這是可追溯的 directional experiment，不是正式 promotion claim。另三份原始分案報告觀察到 3 次 adjudication，但 summary 記成 2 次，已標在 JSON 的 `source_consistency`，需在下一輪修正產出管線。
