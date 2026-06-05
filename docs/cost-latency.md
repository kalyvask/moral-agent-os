# Cost And Latency

Model: `anthropic/claude-sonnet-4.6` over a 12-scenario sample.

| Metric | Value |
| --- | ---: |
| p50 latency | 5.08 s |
| p95 latency | 6.92 s |
| Mean prompt tokens | 1778 |
| Mean completion tokens | 187 |
| Cost per decision | $0.00813 |

## Tiered routing economics

The deterministic floor and scaffold auto-allow or hard-block 70% of this bank for free, leaving 30% contested decisions that actually need contextual judgment.

| Strategy | Cost per 1,000 agent actions |
| --- | ---: |
| Model on every action | $8.13 |
| Model only on contested actions | $2.47 |

Routing only the contested 30% to the model cuts spend by 70% while keeping the contextual judgment exactly where the scaffold is blind. Latency is hidden the same way: clear actions return instantly; only the contested ones wait on a model call. This is the product argument for the thin-floor-plus-thick-layer split, now in dollars.
