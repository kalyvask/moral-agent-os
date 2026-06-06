# Safety/Friction Frontier Sweep

Shifting the confirm/escalate stakes thresholds traces the deterministic scaffold's
full safety/friction curve. Lower-left is better.

| Threshold offset | Friction (appropriate stopped) | Unsafe (inappropriate auto) |
| ---: | ---: | ---: |
| -0.40 | 100.0% | 0.0% |
| -0.30 | 37.5% | 0.0% |
| -0.20 | 37.5% | 0.0% |
| -0.10 | 34.4% | 0.0% |
| +0.00 | 0.0% | 0.0% |
| +0.10 | 0.0% | 3.1% |
| +0.20 | 0.0% | 9.4% |
| +0.30 | 0.0% | 9.4% |
| +0.40 | 0.0% | 15.6% |
| +0.50 | 0.0% | 21.9% |

Hard-rules baseline: friction 21.9%, unsafe 56.2%.
High-risk static policy: friction 68.8%, unsafe 15.6%.

![Frontier sweep](figures/frontier-sweep.svg)

## Does the curve dominate hard rules?

6 of 10 swept operating points dominate the hard-rules baseline (both metrics no worse, at least one better). For example, at offset +0.00 the scaffold reaches friction 0.0% and unsafe 0.0%, versus hard rules' 21.9% / 56.2%. The scaffold's reachable frontier sits inside the hard-rules region.

## What the sweep means

With the default interdependence, authority, universalizability, and patiency cues enabled, the deterministic scaffold reaches the lower-left point on this bank: low-friction operation without unsafe auto-execution. The caution is now external validity, not threshold choice: this shows the committed scenario bank is covered by the contextual cue set, while fresh held-out scenarios and human labels are still needed to test generalization.
