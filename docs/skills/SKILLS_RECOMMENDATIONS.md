# Chronos — Recommended Agent Skills from skills.sh

> Purpose: install only the skills that improve ChronOS implementation quality. Do not blindly install dozens of skills. Too many skills can create conflicting instructions and context noise.

---

## 1. How skills.sh fits ChronOS

The skills.sh directory describes Skills as reusable capabilities for AI agents that can be installed with `npx skills add <owner/repo>`. The directory lists compatibility with multiple coding agents, including Antigravity. It also shows high-install skills such as `frontend-design`, `vercel-react-best-practices`, `web-design-guidelines`, `grill-me`, `improve-codebase-architecture`, `tdd`, `supabase-postgres-best-practices`, and others.

Use skills as reusable guardrails for Antigravity while building ChronOS.

---

## 2. Recommended install set

## Tier 1 — Install first

### 1. `frontend-design` — `anthropics/skills`

Use for:

- ChronOS warm light UI,
- premium command-canvas design,
- avoiding generic dashboard output,
- typography/layout polish,
- interaction hierarchy.

Why:

ChronOS lives or dies by the Command Canvas. This is the highest-value design skill.

Suggested install:

```bash
npx skills add anthropics/skills --skill frontend-design
```

---

### 2. `web-design-guidelines` — `vercel-labs/agent-skills`

Use for:

- landing page,
- visual consistency,
- spacing,
- hierarchy,
- accessible SaaS UI.

Suggested install:

```bash
npx skills add vercel-labs/agent-skills --skill web-design-guidelines
```

---

### 3. `vercel-react-best-practices` — `vercel-labs/agent-skills`

Use for:

- React architecture,
- component structure,
- performance conventions,
- avoiding messy AI-generated frontend code.

Suggested install:

```bash
npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices
```

---

### 4. `supabase-postgres-best-practices` — `supabase/agent-skills`

Use for:

- Supabase schema,
- RLS policies,
- auth/data isolation,
- migrations,
- Postgres conventions.

Suggested install:

```bash
npx skills add supabase/agent-skills --skill supabase-postgres-best-practices
```

---

### 5. `grill-me` — `mattpocock/skills`

Use before implementation phases to force the agent to ask critical questions and expose weak requirements.

Suggested install:

```bash
npx skills add mattpocock/skills --skill grill-me
```

---

### 6. `improve-codebase-architecture` — `mattpocock/skills`

Use before scaffold and after each major feature to prevent architecture decay.

Suggested install:

```bash
npx skills add mattpocock/skills --skill improve-codebase-architecture
```

---

### 7. `tdd` — `mattpocock/skills`

Use for:

- risk engine,
- scheduler functions,
- replanning logic,
- backend deterministic tools,
- schema validation.

Suggested install:

```bash
npx skills add mattpocock/skills --skill tdd
```

---

## Tier 2 — Install when needed

### 8. `to-prd` — `mattpocock/skills`

Use if you want Antigravity to refine this PRD into issue-ready implementation tickets.

```bash
npx skills add mattpocock/skills --skill to-prd
```

---

### 9. `to-issues` — `mattpocock/skills`

Use after architecture is frozen to create task breakdowns.

```bash
npx skills add mattpocock/skills --skill to-issues
```

---

### 10. `github-actions-docs` — `xixu-me/skills`

Use for CI workflow setup.

```bash
npx skills add xixu-me/skills --skill github-actions-docs
```

---

### 11. `playwright-skill` — `testdino-hq/playwright-skill`

Use when UI flows stabilize.

```bash
npx skills add testdino-hq/playwright-skill
```

---

### 12. `taste-skill` — `Leonxlnx/taste-skill`

Use when Antigravity output becomes visually generic. This skill is described as a high-agency frontend taste skill to stop generic UI output.

```bash
npx skills add Leonxlnx/taste-skill
```

---

### 13. Hamel eval skills

Use when evaluating AI outputs.

Recommended:

- `hamelsmu/error-analysis`
- `hamelsmu/generate-synthetic-data`
- `hamelsmu/write-judge-prompt`
- `hamelsmu/validate-evaluator`
- `hamelsmu/eval-audit`

Use for:

- commitment extraction evals,
- risk classification evals,
- negotiation quality evals,
- rescue plan quality evals.

Example:

```bash
npx skills add hamelsmu/error-analysis
npx skills add hamelsmu/generate-synthetic-data
npx skills add hamelsmu/write-judge-prompt
npx skills add hamelsmu/validate-evaluator
npx skills add hamelsmu/eval-audit
```

---

## 3. Patterns.dev skills useful for ChronOS frontend

Patterns.dev lists installable skills across JavaScript, React, and Vue. Relevant React/Vite skills for ChronOS:

### Recommended

```bash
npx skills add PatternsDev/skills --skill react-data-fetching
npx skills add PatternsDev/skills --skill react-render-optimization
npx skills add PatternsDev/skills --skill ai-ui-patterns
npx skills add PatternsDev/skills --skill vite-bundle-optimization
npx skills add PatternsDev/skills --skill view-transitions
```

Use for:

- TanStack Query / frontend data fetching,
- rendering optimization for canvas-heavy UI,
- AI interface patterns,
- Vite bundle quality,
- smoother page transitions.

---

## 4. Skills to avoid for now

Avoid unless there is a direct need:

- video generation skills,
- mobile-app-only design skills,
- Azure-specific skills,
- Lark/Feishu skills,
- overbroad startup skills,
- unrelated cybersecurity mega-packs.

Reason:

ChronOS needs clean implementation focus, not skill clutter.

---

## 5. Practical Antigravity workflow with skills

Use skills in phases:

### Phase A — Project interrogation

Use:

- `grill-me`
- `improve-codebase-architecture`

Goal:

Make Antigravity challenge the architecture before writing code.

### Phase B — Scaffold

Use:

- `vercel-react-best-practices`
- `supabase-postgres-best-practices`
- `frontend-design`

Goal:

Set up clean frontend/backend/database conventions.

### Phase C — Core backend

Use:

- `tdd`
- `improve-codebase-architecture`

Goal:

Build deterministic tools and schemas before agent orchestration.

### Phase D — Product UI

Use:

- `frontend-design`
- `web-design-guidelines`
- `taste-skill`
- `ai-ui-patterns`

Goal:

Make the Command Canvas stand out.

### Phase E — Evaluation and polish

Use:

- Hamel eval skills
- `playwright-skill`
- `github-actions-docs`

Goal:

Add quality gates, tests, and defensibility.

---

## 6. Warning

Do not let installed skills override ChronOS product intent.

ChronOS product truth comes from:

1. `docs/chronos/MASTER_CONTEXT.md`
2. `docs/chronos/PROJECT_REQUIREMENTS.md`
3. `docs/chronos/DESIGN_SPECIFICATIONS.md`

Skills are implementation helpers, not product owners.
