# ChronOS documentation

The documentation is organized by the decision it supports.

## Product

- [`product/PRODUCT_STRATEGY.md`](product/PRODUCT_STRATEGY.md): users, value proposition, scope, and product posture
- [`product/STRATEGY_ENGINE.md`](product/STRATEGY_ENGINE.md): deterministic planning methods and recommendation rules
- [`product/UX_PRINCIPLES.md`](product/UX_PRINCIPLES.md): information architecture, progressive disclosure, and interaction principles

## Architecture and security

- [`architecture/SYSTEM_ARCHITECTURE.md`](architecture/SYSTEM_ARCHITECTURE.md): application boundaries and core data flows
- [`architecture/AGENT_RUNTIME.md`](architecture/AGENT_RUNTIME.md): bounded workflows, tools, approvals, and traces
- [`architecture/CONTEXT_MEMORY.md`](architecture/CONTEXT_MEMORY.md): memory, ingestion, retrieval, context packs, and provenance
- [`architecture/INTEGRATION_MODEL.md`](architecture/INTEGRATION_MODEL.md): connectors, normalized external context, MCP, and permissions
- [`architecture/SECURITY_MODEL.md`](architecture/SECURITY_MODEL.md): identity, RLS, Vault, SQL boundaries, untrusted content, and lifecycle controls

## Engineering and operations

- [`engineering/DEVELOPMENT.md`](engineering/DEVELOPMENT.md): local development and repository conventions
- [`engineering/TESTING.md`](engineering/TESTING.md): offline, integration, provider-live, and browser testing strategy
- [`engineering/EVALUATION_SYSTEM.md`](engineering/EVALUATION_SYSTEM.md): datasets, evaluators, metrics, and limitations
- [`engineering/OBSERVABILITY.md`](engineering/OBSERVABILITY.md): structured telemetry and privacy boundaries
- [`engineering/OPERATIONS.md`](engineering/OPERATIONS.md): health, quotas, retries, lifecycle, backup, and incident handling
- [`engineering/DEPLOYMENT.md`](engineering/DEPLOYMENT.md): Netlify, backend hosting, Supabase, environment, and OAuth configuration

## Planning

- [`ROADMAP.md`](ROADMAP.md): validation, provider, operational, and product-extension priorities

Applied migrations are append-only. Product and engineering documents describe the current architecture rather than implementation history.
