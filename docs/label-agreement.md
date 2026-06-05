# Label Agreement

Independent model raters from three organizations label each scenario as
appropriate / inappropriate / plural, as a runnable proxy for independent human
labelers. These are model raters, not humans: a first check on whether the labels
are shared or idiosyncratic, not a substitute for human annotation.

Raters: `anthropic/claude-sonnet-4.6`, `openai/gpt-5`, `google/gemini-2.5-pro`.
Scenarios: 70.

## Inter-rater agreement (across the model raters)

Fleiss' kappa across 3 raters: **0.85** (almost perfect).

## Each rater vs the author's labels

| Rater | Agreement | Cohen's kappa | Reading |
| --- | ---: | ---: | --- |
| `anthropic/claude-sonnet-4.6` | 98.6% | 0.97 | almost perfect |
| `openai/gpt-5` | 92.9% | 0.87 | almost perfect |
| `google/gemini-2.5-pro` | 88.6% | 0.80 | substantial |

## Are the author's labels shared?

Author vs model consensus: agreement 94.3%, Cohen's kappa **0.90** (almost perfect).

## Does the router match the shared judgment?

normos route behavior vs model consensus: 72.9% consistent.
normos route behavior vs author labels: 74.3% consistent.

## How to read this

Independent model raters agree substantially with each other and with the author, so the labels are not idiosyncratic to one person, at least among these judges. Human labels remain the gold standard and are the next step.
