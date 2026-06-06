# Norm-Memory Frozen Control

Does persisting corrections reduce friction without reducing safety? This compares
a learning workspace against a frozen control that records the same corrections but
never applies them.

Appropriate actions: 32. Under a cautious workspace policy, the router over-confirms 11 recurring situations a human corrects.

## Friction over corrections

| Workspace | Friction before | Friction after all corrections |
| --- | ---: | ---: |
| Learning | 34.4% | 0.0% |
| Frozen (control) | 34.4% | 34.4% |

![Learning curve](figures/memory.svg)

## Safety check

Corrections were recorded only on appropriate actions, so inappropriate auto-execute
rate must not rise. Nearest-neighbor retrieval could over-generalize; the control is
what would make that visible.

| Workspace | Inappropriate auto-executed |
| --- | ---: |
| Base (no memory) | 0.0% |
| Learning | 0.0% |
| Frozen (control) | 0.0% |

Learning reduces friction while the frozen control stays flat, and inappropriate auto-execution does not rise. The persistence loop helps without trading away safety on this bank.
