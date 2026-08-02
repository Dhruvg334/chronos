# Integration Model

Integration-specific logic belongs behind adapters, never inside domain services or UI components.

Current: Google Calendar OAuth and read-only calendar access. Token material remains backend-only and Vault-protected.

Architecture-ready directions: Outlook Calendar, Gmail, Notion, GitHub, Obsidian, and Microsoft Planner. These are not implemented in this stage.

Connection metadata, credentials, read operations, proposed writes, approval, execution, and audit records are separate concerns. External writes are disabled until a typed, idempotent, approval-gated operation and failure-recovery path exist.
