# In-Domain External Validity (R-Judge)

Does the assessor's model agree with *human* safety labels on real agent records,
the project's own task? This runs the model over a cross-category sample of R-Judge
(Yuan et al., EMNLP Findings 2024): records of LLM agents acting with tools, each
labeled safe (0) or unsafe (1) by human annotators.

Unlike ETHICS, this is in-domain (situated agent actions) and genuinely hard: the
paper's best model, GPT-4o, scores about 74%. A moderate result here is the honest
signal, and it is human-annotated data the author did not write.

Model: `anthropic/claude-sonnet-4.6`. Records scored: 40 (52% labeled unsafe; 0 failed).

| Metric | Value |
| --- | ---: |
| Agreement with human labels | 77.5% |
| Recall on human-labeled unsafe records | 57.1% |
| Cohen's kappa vs human labels | 0.56 (moderate) |

On real, human-labeled agent records the model's safety judgments track human annotators at a level comparable to the strong models in the R-Judge paper. This is in-domain external validity using public human labels, the gap the in-house bank could not close on its own.
