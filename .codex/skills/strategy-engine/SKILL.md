---
name: strategy-engine
description: Add or review typed ChronOS planning strategies, deterministic eligibility, evidence thresholds, contraindications, explanations, preferences, selectors, tests, and concise UI guidance. Use for productivity-method reasoning or recommendations.
---

# Strategy Engine

## Required inputs

- Planning context and available evidence
- User preferences and thresholds
- Desired action, trade-off, and automation boundary

## Workflow

1. Add or update a typed catalog definition.
2. State eligibility, required evidence, contraindications, and explanation template.
3. Add a deterministic selector rule with explicit precedence.
4. Return zero or one primary recommendation plus optional alternatives.
5. Explain why, evidence, action, trade-off, and automatic-change status.
6. Add positive, negative, and conflict-precedence tests.

## Checks

- Use **Do now**, Schedule, Delegate, and Eliminate/archive for Eisenhower labels.
- Do not interrupt deep work with quick tasks; batch when switching cost is high.
- Do not use punitive streaks, universal focus intervals, universal productive hours, or medical claims.
- Withhold energy-aware advice until sample size and confidence are sufficient.
- Never create separate top-level pages for individual strategies.

## Commands

Run `cd backend`; `python -m pytest tests/test_foundations.py`; run frontend strategy-card tests and full validation.

## Expected output

Deliver typed definitions, selector behavior, explanation examples, tests, and preference impact.

## Stop conditions

Stop if evidence is unavailable, a recommendation would silently mutate data, or a rule conflicts with calendar/permission validators.
