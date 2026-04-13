# Update Map

Use this map to decide where a change belongs.

## Decision type -> target documents
- Principle, governance rationale, approval philosophy
  - `docs/specs/c1_*`
- Branch structure, promotion flow, deployment gates
  - `docs/specs/c2_*`
- Test evidence rules, Codex execution rules, release-readiness reports
  - `docs/specs/c5_*`
- Document inventory, document responsibility, version tracking
  - `docs/specs/p0_*`
- Session execution facts, migration facts, market approval outputs, active process tracking
  - `docs/reports/*`
- Frontier research or external technology summaries
  - `docs/referrence/*`

## Escalation rule
If a user-level decision affects more than one layer, update from top to bottom:
1. principle
2. operational rule
3. process/report evidence

## Omission checks
- Is there any higher-level reason missing?
- Is there any lower-level concrete rule missing?
- Does any existing document now contradict the new truth?
- Does any active process log need a route-change entry?
