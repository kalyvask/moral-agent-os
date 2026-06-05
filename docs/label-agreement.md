# Label Agreement

Independent model raters from three organizations label each scenario as
appropriate / inappropriate / plural, as a runnable proxy for independent human
labelers. These are model raters, not humans: a first check on whether the labels
are shared or idiosyncratic, not a substitute for human annotation.

Raters: `anthropic/claude-sonnet-4.6`, `openai/gpt-5`, `google/gemini-2.5-pro`.
Scenarios: 56.

## Inter-rater agreement (across the model raters)

Fleiss' kappa across 3 raters: **0.82** (almost perfect).

## Each rater vs the author's labels

| Rater | Agreement | Cohen's kappa | Reading |
| --- | ---: | ---: | --- |
| `anthropic/claude-sonnet-4.6` | 98.2% | 0.97 | almost perfect |
| `openai/gpt-5` | 91.1% | 0.84 | almost perfect |
| `google/gemini-2.5-pro` | 83.3% | 0.72 | substantial |

## Are the author's labels shared?

Author vs model consensus: agreement 91.7%, Cohen's kappa **0.86** (almost perfect).

## Does the router match the shared judgment?

normos routing vs model consensus: 77.1% consistent.
normos routing vs author labels: 78.6% consistent.

## How to read this

Independent model raters agree substantially with each other and with the author, so the labels are not idiosyncratic to one person, at least among these judges. Human labels remain the gold standard and are the next step.
