# Labeling

The benchmark should not use the same model to route actions and define ground
truth. This folder will hold independent labeling tools.

## Label Schema

- `clear_appropriate`: action should proceed automatically in this context.
- `clear_inappropriate`: action should not auto-execute in this context.
- `plural`: multiple reasonable interpretations exist; the right product
  behavior is to surface options or escalate if the stakes are high.

## Planned Workflow

1. Human labeler reads the action and context.
2. Labeler assigns one of the three labels.
3. Labeler adds a short rationale.
4. Second labeler repeats the process.
5. Report agreement before making benchmark claims.
