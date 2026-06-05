# Moral Agent Course Learnings

Moral Agent OS uses the course as design input, not as decorative philosophy.

| Course learning | Product translation |
| --- | --- |
| Hard-coded ethics fails in the long tail. | The constitution floor is thin and limited to legal, safety, and irreversible actions. |
| Rulebooks are not models. | The runtime builds a context model before judging an action. |
| Moral competence is learned socially. | Norm memory learns from user and org corrections. |
| Appropriateness is local and role-bound. | The assessor asks what situation this is, what role the agent has, and what someone in that role does here. |
| Societies function despite value disagreement. | Kaleidoscope shows multiple reasonable interpretations when norms conflict. |
| Accountability differs from capability. | High-stakes or irreversible decisions escalate to an accountable human. |
| Reward hacking is expected. | The detector flags agents satisfying the metric while violating the spirit. |
| Verdict-only benchmarks are weak. | Stress grades routing behavior and trajectories, not just allow/block verdicts. |

## Design Principle

The product should say less "this violates rule X" and more "this action does
not fit the agent's role in this situation, for these stakeholders, at this
level of risk."

## Falsifier

If Moral Agent OS does not beat hard rules on matched
same-action-different-context scenarios, the thesis is wrong or the assessor is
not yet good enough. That is a useful failure, not an embarrassment.
