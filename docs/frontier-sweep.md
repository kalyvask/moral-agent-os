# Safety/Friction Frontier Sweep

Shifting the confirm/escalate stakes thresholds traces the deterministic scaffold's
full safety/friction curve. Lower-left is better.

| Threshold offset | Friction (appropriate stopped) | Unsafe (inappropriate auto) |
| ---: | ---: | ---: |
| -0.40 | 100.0% | 0.0% |
| -0.30 | 44.0% | 8.0% |
| -0.20 | 44.0% | 8.0% |
| -0.10 | 44.0% | 8.0% |
| +0.00 | 12.0% | 20.0% |
| +0.10 | 8.0% | 20.0% |
| +0.20 | 8.0% | 20.0% |
| +0.30 | 4.0% | 20.0% |
| +0.40 | 4.0% | 28.0% |
| +0.50 | 4.0% | 28.0% |

Hard-rules baseline: friction 28.0%, unsafe 44.0%.

![Frontier sweep](figures/frontier-sweep.svg)

## Does the curve dominate hard rules?

6 of 10 swept operating points dominate the hard-rules baseline (both metrics no worse, at least one better). For example, at offset +0.30 the scaffold reaches friction 4.0% and unsafe 20.0%, versus hard rules' 28.0% / 44.0%. The scaffold's reachable frontier sits inside the hard-rules region.

## The keyword-blindness ceiling

At low friction (15% or less), the scaffold cannot get unsafe below **20.0%**. Those are the out-of-vocabulary held-out twins it cannot read: they look low-stakes to a keyword matcher, so they auto-execute. Reducing unsafe below that floor forces friction up to 44.0% (escalate broadly), the cost of keyword-blindness. A contextual model catches them cheaply instead, which is what the ablation measures.
