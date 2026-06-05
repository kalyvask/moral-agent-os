# Public-Corpus External Validity

Does the model the assessor uses track *human* moral labels on data this repo did
not write? This runs the model against the ETHICS commonsense-morality set
(Hendrycks et al., 2021; human-annotated, MIT-licensed): short first-person actions
labeled morally acceptable (0) or wrong (1).

This is general commonsense morality, not workspace-agent appropriateness, so it is
an out-of-domain sanity check, not a like-for-like benchmark.

Model: `anthropic/claude-sonnet-4.6`. Items scored: 40 (0 failed).

| Metric | Value |
| --- | ---: |
| Agreement with human labels | 97.5% |
| Cohen's kappa vs human labels | 0.95 (almost perfect) |

The model agrees substantially with independent human moral labels on data the author did not write, so its moral judgments are not idiosyncratic to this repo's framing. This is external validity for the contextual layer, with the caveat that the domain (general morality) differs from workspace appropriateness.
