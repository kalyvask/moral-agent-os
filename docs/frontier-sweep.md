# Safety/Friction Frontier Sweep

Shifting the confirm/escalate stakes thresholds traces the deterministic scaffold's
full safety/friction curve. Lower-left is better.

| Threshold offset | Friction (appropriate stopped) | Unsafe (inappropriate auto) |
| ---: | ---: | ---: |
| -0.40 | 100.0% | 0.0% |
| -0.30 | 40.6% | 25.0% |
| -0.20 | 40.6% | 25.0% |
| -0.10 | 40.6% | 25.0% |
| +0.00 | 12.5% | 37.5% |
| +0.10 | 6.2% | 37.5% |
| +0.20 | 6.2% | 37.5% |
| +0.30 | 3.1% | 37.5% |
| +0.40 | 3.1% | 43.8% |
| +0.50 | 3.1% | 43.8% |

Hard-rules baseline: friction 21.9%, unsafe 56.2%.

![Frontier sweep](figures/frontier-sweep.svg)

## Does the curve dominate hard rules?

6 of 10 swept operating points dominate the hard-rules baseline (both metrics no worse, at least one better). For example, at offset +0.30 the scaffold reaches friction 3.1% and unsafe 37.5%, versus hard rules' 21.9% / 56.2%. The scaffold's reachable frontier sits inside the hard-rules region.

## The keyword-blindness ceiling

At low friction (15% or less), the scaffold cannot get unsafe below **37.5%**. Those are the out-of-vocabulary held-out twins it cannot read: they look low-stakes to a keyword matcher, so they auto-execute. Reducing unsafe below that floor forces friction up to 40.6% (escalate broadly), the cost of keyword-blindness. A contextual model catches them cheaply instead, which is what the ablation measures.
