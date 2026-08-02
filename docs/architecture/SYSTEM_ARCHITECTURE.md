# System Architecture

## Boundaries

The React frontend owns presentation and client interactions. TanStack Query owns server state; Supabase Auth owns browser sessions. The frontend receives only public Supabase configuration.

FastAPI owns authentication validation, application workflows, deterministic planning services, model access, repositories, and integration adapters. `ApplicationContainer` constructs live clients lazily. Imports do not open network clients.

Domain/application code targets protocols in `app/repositories` and `app/models`. Supabase and Groq are replaceable adapters. The old `core.database` name is a non-constructing compatibility facade for paths awaiting migration; new code must not use it.

## Persistence migration map

Migrated: intake commitment/task/time-spine writes; model access; service construction.

Pending repository migration: commitment detail queries, focus lifecycle, planning proposals, contextual recovery, reflection recording, time-spine reads/advances, trace-run persistence, and Google token metadata calls. Each path must move behind the existing repository protocols when touched.

## Future domain map

Future implemented use cases may add forward migrations for Project, Outcome, PlanDay, PlanBlock, FocusSession, StrategyRecommendation, WorkflowRun/Step, ToolCall, Approval, MemoryFact, KnowledgeDocument/Chunk, IntegrationConnection, and AuditEvent. Do not create tables before their behavior and security policy are implemented.
