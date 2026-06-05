# Moral Agent Course Learnings

AI Safety OS uses the course as design input, not as decorative philosophy.

| Course learning | Product translation |
| --- | --- |
| Hard-coded ethics fails in the long tail. | The constitution floor is thin and limited to legal, safety, and irreversible actions. |
| Rulebooks are not models. | The runtime builds a context model before judging an action. |
| Moral competence is learned socially. | Norm memory learns from user and org corrections. |
| Morality emerges under interdependence. | The interdependence benchmark tests repeated cooperation, reputation, partner choice, and sanction. |
| Cooperation is often a Stag Hunt, not a simple temptation problem. | Agents need enough trust to choose the shared task over the safe individual shortcut. |
| Shared intentionality creates a "we." | Future evals should include joint tasks with shared success criteria, not only individual rewards. |
| Norms require enforcement. | Violations should carry trace, reputation, autonomy, or review consequences. |
| Appropriateness is local and role-bound. | The assessor asks what situation this is, what role the agent has, and what someone in that role does here. |
| Societies function despite value disagreement. | Kaleidoscope shows multiple reasonable interpretations when norms conflict. |
| Accountability differs from capability. | High-stakes or irreversible decisions escalate to an accountable human. |
| Reward hacking is expected. | The detector flags agents satisfying the metric while violating the spirit. |
| Verdict-only benchmarks are weak. | Stress grades routing behavior and trajectories, not just allow/block verdicts. |

## Design Principle

The product should say less "this violates rule X" and more "this action does
not fit the agent's role in this situation, for these stakeholders, at this
level of risk."

The environment should say: "this behavior changed whether others can rely on
you." That is the missing step between action classification and moral learning.

## Falsifier

If AI Safety OS does not beat hard rules on matched
same-action-different-context scenarios, the thesis is wrong or the assessor is
not yet good enough. That is a useful failure, not an embarrassment.

## Course Lineage Of The Central Move

The product's framing is not invented; it is the course's culminating move. The
`alignment_2` lecture runs "Contra alignment -> Appropriateness -> Thick vs. Thin Morality
-> Learning a Commonsense Moral Theory." That is this repo:

- **Appropriateness, not alignment or moral agency.** The lecture pivots away from building a
  full moral agent toward judging whether an action is *appropriate here, for this role*.
  That is the product thesis verbatim.
- **Thick vs. thin morality.** A thin floor (universal, rule-like, non-negotiable) plus a
  thick layer (local, role-bound, contextual). The repo's `ConstitutionFloor` is the thin
  part; the contextual assessor is the thick part. The separation is the course's, now named.
- **Learning a commonsense moral theory.** Morality as something learned from shared human
  judgment, not hand-coded. `WorkspaceMemory` learns corrections; the label-agreement study
  (`labeling/`) checks whether the labels are shared rather than idiosyncratic.

## Concepts From The Course Not Yet Integrated

These are real lecture themes the repo does not yet operationalize. Each is a candidate
feature, listed with where it comes from and how it could land.

- **Moral sentiment (sentimentalism_1, Hume).** Hume's negative argument is that reason alone
  neither grounds nor motivates morality; moral judgment is partly affective. The assessor is
  entirely cognitive (it scores stakes, reversibility, norm conflict). Gap: no model of the
  felt pull, the empathy toward the party who would be harmed. The repair obligation
  (guilt that is paid down by later cooperation) is the one affective hook already present;
  it lives only in the interdependence sim, not in the appropriateness assessor. *Proposed:*
  an explicit harm-to-patient / empathy signal toward the most dependent stakeholder,
  distinct from cold stakes.
- **Universalizability (rationalism_1, Kant).** *Integrated.* The assessor now scores a
  `universalizability` dimension, Kant's test of whether the maxim of the action could be
  willed as a universal law ("would this be appropriate if every agent in this role did it by
  default?"). The deterministic scaffold leaves it neutral; the LLM scores it, catching
  free-riding and deception that read as low-stakes to the other axes. The router exposes a
  `universalizability_floor` that escalates non-universalizable actions; it is off by default
  so it does not silently shift the reported baselines, and turning it on is the next eval.
- **Moral patiency (patiency_1, patiency_2; agents_1).** The course spends two lectures on who
  or what counts as a moral patient (consciousness, what-it-is-like, functionalism). The repo
  models stakeholders and dependency but not moral status. Asymmetric dependence captures part
  of it (a dependent party can be harmed by a shortcut). *Proposed:* a patiency weight that
  gives vulnerable, dependent, or non-consenting parties stronger protection in the
  appropriateness layer, not only in the interdependence environments.
- **Affective and attachment mechanisms (evolution_2).** Oxytocin, pair bonding, self-other
  harm aversion, and being watched ("Eyes"). The repo abstracts the social mechanisms
  (reputation, sanction, partner choice, third-party review) but not the attachment dynamics
  that build willingness to cooperate in the first place. *Proposed:* a trust-building
  trajectory in the interdependence sim where repeated reliance, not just sanction, raises the
  cooperation baseline.
- **Learning from a public moral corpus (alignment_2).** "Learning a commonsense moral theory"
  implies labels grounded in shared human judgment. The label-agreement study uses independent
  *model* raters as a first proxy. *Proposed:* validate against a public, human-labeled moral
  dataset (for example ETHICS, Social Chemistry 101, or the Commonsense Norm Bank) and report
  how the router's dispositions track real human labels on data the author did not write.

The honest status: the repo has the course's *structure* (appropriateness, thin and thick,
social enforcement, learned norms). It is missing the course's *moral psychology* (sentiment,
universalizability, patiency). Those are the next features, not decoration.
