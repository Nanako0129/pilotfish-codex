# Astra root-model smoke observations

This contributor-run smoke compared personal Sol high, Sol xhigh and Astra low
root configurations on one small bug. Astra completed the direct case faster,
but its Standard API-equivalent cost was higher. These observations support an
optional speed-oriented root choice; they do not justify replacing the
project's Luna-first default.

## Setup and limits

| Property | Recorded condition |
| --- | --- |
| Client | Codex CLI 0.153.3 |
| Task | Repair stale committed usage while preserving immutable message snapshots |
| Direct cases | Root works without a child |
| Delegated cases | Exactly one executor child, Luna max |
| Order | D-A, D-B, D-C, E-C, E-B, E-A, then fresh E-C-R1, E-B-R1, E-A-R1 |
| Deadlines | Initial cases: 180 seconds; authorized fresh delegated retries: 360 seconds |
| Sample | One completed observation per configuration and shape |

The [fixture](./fixture) comes from
[Pilotfish commit 863b117](https://github.com/Nanako0129/pilotfish/tree/863b117b9da42179c5bb77a05158920fbc092ee2/benchmarks/dispatch-brake/fixture)
and retains its MIT license. [Direct](./direct.txt) and
[delegated](./delegated.txt) prompts are included. Personal user-level
instructions were also loaded during the original runs. Raw sessions and those
private instructions are not published, so this is not a reproducible snapshot
of the entire original environment or a test of the current upstream defaults.

## Results

| Shape | Root | Seconds | Standard API-equivalent USD |
| --- | --- | ---: | ---: |
| Direct | Sol xhigh | 97.142 | 0.33487840 |
| Direct | Sol high | 95.031 | 0.22179280 |
| Direct | Astra low | 43.940 | 0.35530600 |
| Delegated, fresh retry | Sol xhigh | 208.589 | 0.27319512 |
| Delegated, fresh retry | Sol high | 210.095 | 0.25418616 |
| Delegated, fresh retry | Astra low | 163.280 | 0.73359524 |

All six completed cases passed both original tests and the external
[acceptance check](./acceptance.mjs). The first three delegated attempts reached
the deadline after producing artifacts that passed acceptance, but before the
parent completed its turn. They remain censored observations, not successes:

| Case | Root | Deadline | Reported-usage cost lower bound, USD |
| --- | --- | ---: | ---: |
| E-C | Sol high | 180 seconds | 0.20262536 |
| E-B | Astra low | 180 seconds | 1.02521412 |
| E-A | Sol xhigh | 180 seconds | 0.18539636 |

The Astra delegated retry made seven 10-second wait calls. Sol high made one
360-second wait, and Sol xhigh made two 60-second waits. Waiting behavior and
cache hit rates differed; their causal contribution was not isolated. There
was no Astra executor trial, broad quality comparison or statistical ranking.

## Accounting

[results.json](./results.json) contains allowlisted aggregate token categories,
fixture and result hashes, statuses and the dated
[OpenAI Standard rates](https://developers.openai.com/api/docs/pricing).
Codex input counts include cached input: uncached input is total input minus
cached input. Output already includes reasoning. Exclusive root and child
usage was counted once.

```text
API equivalent = sum over models of
  (uncached input × input rate + cached input × cache rate
   + cache creation × write rate + output × output rate) / 1,000,000
```

Standard was requested, but the response tier was not surfaced. These are
conditional Standard token charges, not verified invoices. Cancelled calls may
have unreported usage. Subscription quota attribution is inconclusive because
the readings were integer account-level counters shared with the controller.
Purchased-credit prices and included subscription limits are distinct, as the
[official rate card](https://help.openai.com/en/articles/11481834-chatgpt-rate-card-business-enterpriseedu/)
explains. No subscription multiplier is inferred from API prices or community
estimates.

## Offline checks

From the repository root, verify every published cost without calling a model:

```bash
python3 docs/benchmarks/astra-root-smoke/verify_costs.py
```

The included fixture deliberately contains the bug. After a separately
approved implementation run in a disposable copy, check that completed copy:

```bash
node docs/benchmarks/astra-root-smoke/acceptance.mjs ./completed-fixture
npm --prefix ./completed-fixture test
```

The acceptance check covers committed and provisional usage, prior-state
immutability, canonical-message aliasing, unknown IDs and unrelated events.
The public files reproduce the arithmetic and acceptance checks, not the
original private context, exact timing or future quota consumption.
