---
name: frontend-product-ui
description: Build or review ChronOS React product interfaces, navigation, responsive layouts, asynchronous states, design tokens, and accessibility. Use for Today, Inbox, Plan, Focus, auth, demo, settings, or shared UI component work.
---

# Frontend Product UI

## Required inputs

- User goal and route
- Auth/public boundary
- API contract and pending/success/error/empty states
- Mobile and desktop expectations

## Workflow

1. Read `docs/product/UX_PRINCIPLES.md` and inspect existing primitives/tokens.
2. Keep primary navigation limited to Today, Inbox, and Plan.
3. Design the smallest useful hierarchy with progressive disclosure.
4. Use TanStack Query for server state; keep Zustand for justified client-only state.
5. Implement accessible labels, keyboard focus, responsive layout, and actionable errors.
6. Add React Testing Library coverage before validation.

## Checks

- No private content flashes before auth resolves.
- Public demo is static and makes no protected request.
- Async actions expose pending, success where useful, error, and safe retry.
- Feature components use semantic tokens, not arbitrary colors.
- Today shows one status, next action, primary CTA, ordered plan, and at most one strategy card.

## Commands

Run `cd frontend`; `npm run typecheck`; `npm run lint`; `npm run test -- --run`; `npm run build`.

## Expected output

Deliver tested source-owned components, route behavior, responsive states, and exact manual test steps.

## Stop conditions

Stop if the API/auth contract is unknown and guessing could expose data, or if the request requires an unapproved external write.
