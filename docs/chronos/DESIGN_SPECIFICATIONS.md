# Chronos — Design Specifications Document

> Product: **ChronOS**  
> Design target: warm, light, premium, dynamic command-canvas experience  
> Warning: do not design this like a basic dashboard, Kanban board, task table, or chatbot panel.

---

## 1. Design Vision

ChronOS should feel like a calm, intelligent operating system for time.

The interface should communicate:

- time is alive,
- plans adapt,
- the agent is acting,
- risk is visible,
- the user stays in control,
- execution is always clear.

ChronOS should look premium enough for a frontend-sensitive judge, but it must remain usable. Visual polish cannot come at the cost of clarity.

---

## 2. Brand Direction

### 2.1 Logo Treatment

Use **ChronOS**.

- “Chron” = time.
- “OS” = operating system.
- “OS” should be a different warm accent color.

Recommended:

- Chron: deep warm charcoal
- OS: amber / copper / terracotta

### 2.2 Brand Personality

ChronOS is:

- calm,
- decisive,
- intelligent,
- warm,
- high-agency,
- trustworthy,
- strategic.

ChronOS is not:

- cute,
- noisy,
- motivational-poster-like,
- cold enterprise,
- cyberpunk,
- gamified for the sake of gamification.

### 2.3 Voice in UI

Use calm operational language.

Good:

- “Your plan has drifted.”
- “This commitment is now at risk.”
- “I found a viable recovery path.”
- “This deadline needs scope reduction.”
- “Approve calendar update?”

Bad:

- “You failed.”
- “Emergency!”
- “Hustle harder.”
- “Motivation quote of the day.”

---

## 3. Visual System

## 3.1 Theme

Primary theme: **warm light mode**.

The UI should have:

- soft warm backgrounds,
- high contrast warm text,
- elegant accent color,
- subtle borders,
- controlled shadows,
- restrained motion.

## 3.2 Color Palette

### Background

| Token | Color |
|---|---|
| `bg-warm-ivory` | `#FAF6EF` |
| `bg-soft-cream` | `#FFF9F0` |
| `surface-warm` | `#F4EDE3` |
| `surface-card` | `#FFFFFF` |
| `border-warm` | `#E7DCCB` |

### Text

| Token | Color |
|---|---|
| `text-primary` | `#211B16` |
| `text-secondary` | `#5E5147` |
| `text-muted` | `#8A7C70` |

### Accent

| Token | Color |
|---|---|
| `accent-amber` | `#D88A21` |
| `accent-terracotta` | `#C96F45` |
| `accent-copper` | `#9E4F2F` |

### Risk

| Risk | Color |
|---|---|
| Stable | `#6F8A4D` |
| Watch | `#D89B2B` |
| At Risk | `#C86A2D` |
| Critical | `#A63A2E` |
| Rescue Required | `#6F1D1B` |

### Intelligence / System Colors

| Purpose | Color |
|---|---|
| AI glow | `#F0C66A` |
| Calendar | `#557A95` |
| Reflection | `#7B5E7E` |

Risk should not rely only on color. Always pair color with label, icon, or text.

---

## 3.3 Typography

Recommended fonts:

- Headings: Inter, Satoshi, Geist, or Instrument Sans
- Body: Inter, Geist, or system sans
- Trace logs: JetBrains Mono or Geist Mono

Rules:

- Use large, confident headings.
- Keep body text tight.
- Use strong numeric hierarchy for time and risk.
- Do not overuse monospace.

---

## 3.4 Shape Language

Use:

- rounded rectangles,
- oval command pills,
- soft shadows,
- thin warm borders,
- timeline nodes,
- flowing spine lines,
- subtle glow for active intelligence.

Avoid:

- heavy gradients,
- glassmorphism everywhere,
- neon cyberpunk,
- cartoon illustrations,
- random icon clutter.

---

## 4. Information Architecture

## 4.1 Primary Navigation

Use a centered oval navbar.

Items:

- Command
- Inbox
- Time Spine
- Calendar
- Rescue
- Reflection

Right side:

- Calendar sync state
- Time Health Score
- User profile/settings

## 4.2 Routes

### Public

- `/`
- `/demo`
- `/login`
- `/signup`

### App

- `/command`
- `/inbox`
- `/commitments/:id`
- `/calendar`
- `/rescue`
- `/reflection`
- `/settings`
- `/agent-runs/:id`

---

## 5. Landing Page

## 5.1 Hero

Main headline:

**Your time does not need another list. It needs an operating system.**

Subheadline:

**ChronOS captures your commitments, maps their time-spines, watches reality drift, and replans before deadlines break.**

Hero visual:

- central command canvas mockup,
- animated time spine,
- one task drifting into risk,
- ChronOS recalculating,
- warm light background.

CTA:

- “Open ChronOS”
- “View Live Demo”

## 5.2 Problem Section

Compare:

### Traditional productivity tools

- store tasks,
- show calendars,
- send reminders,
- assume plans remain valid.

### ChronOS

- clarifies commitments,
- detects drift,
- calculates risk,
- replans,
- rescues,
- learns.

## 5.3 How It Works

Four-step visual:

1. Dump commitments
2. Build time-spines
3. Monitor drift
4. Replan and rescue

## 5.4 Feature Showcase

Cards:

- Brain Dump Inbox
- Time Spine
- Drift Radar
- Rescue Mode
- Negotiator Agent
- Reflection Engine
- Google Calendar Sync
- Agent Trace

## 5.5 Demo Scenario Section

Interactive scenarios:

- Hackathon week
- Interview week
- Assignment crisis
- Busy professional day

Each scenario should animate:

1. extraction,
2. risk scoring,
3. time spine creation,
4. drift event,
5. replan,
6. rescue.

---

## 6. App Shell

## 6.1 Desktop Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Oval Nav + Date + Time Health + Calendar Sync + Profile       │
├─────────────────┬───────────────────────────┬────────────────┤
│ Time Spine      │ Active Focus Console       │ Agent Console  │
│ Commitments     │ Current mission            │ Actions/trace  │
│ Milestones      │ Next action                │ Replan notes   │
│ Risk nodes      │ Timer / done condition     │ Tool calls     │
├─────────────────┴───────────────────────────┴────────────────┤
│ Drift Radar + Decision Dock                                   │
└──────────────────────────────────────────────────────────────┘
```

## 6.2 Global States

Design these states deliberately:

- empty state,
- loading state,
- agent thinking state,
- calendar syncing state,
- risk recalculating state,
- replan pending approval,
- rescue mode active,
- reflection due,
- error state.

---

## 7. ChronOS Command Canvas

This is the product’s signature interface.

## 7.1 Time Spine Panel

Purpose:

Show commitments as living paths across time.

Elements:

- timeline line,
- commitment nodes,
- milestone nodes,
- feedback gates,
- buffer zones,
- deadline markers,
- risk heat,
- rescue threshold.

Interactions:

- click node to inspect,
- hover for reason,
- drag flexible blocks,
- filter by day/week/project,
- toggle risk overlay.

## 7.2 Active Focus Console

Purpose:

Tell the user exactly what to do now.

Elements:

- Current Mission
- Why Now
- Next Action
- Done Condition
- Time Available
- Materials Needed
- Start Button
- Mark Blocked
- Took Longer
- Finished Early
- Skip / Defer

The Active Focus Console should be the visual center. It should be larger, calmer, and cleaner than surrounding panels.

## 7.3 Agent Console

Purpose:

Make agentic behavior visible.

Events:

- “Fetched 7 calendar events.”
- “Detected 2.5h focus window.”
- “Risk increased from Watch to At Risk.”
- “Moved shallow task to tomorrow.”
- “Created proposed focus block.”
- “Rescue Mode available.”

Default view should be human-readable. Technical payloads can be expandable.

## 7.4 Drift Radar

Purpose:

Show plan-vs-reality mismatch.

Drift cards should show:

- drift type,
- severity,
- source,
- affected commitment,
- suggested response.

Examples:

- “Coding block overran by 38 minutes.”
- “New calendar event conflicts with deep work block.”
- “Energy marked low; move high-cognitive task.”
- “Task scope increased.”

## 7.5 Decision Dock

Purpose:

Human-in-the-loop approval area.

Actions:

- Accept replan
- Reject replan
- Edit plan
- Create calendar block
- Enter Rescue Mode
- Draft negotiation message
- Defer low-impact task

Decision buttons must be clear and calm.

---

## 8. Inbox Design

## 8.1 Brain Dump Input

Large input surface with example prompts.

Input modes:

- text,
- voice,
- bulk paste,
- demo scenario.

## 8.2 Extraction Review

After extraction, show grouped cards:

- Hard Deadlines
- Events
- Habits
- Waiting-On
- Unclear Items
- Quick Actions

Each card includes:

- AI confidence,
- editable fields,
- missing info,
- approve/reject.

## 8.3 Clarification Questions

Ask only focused questions:

- “When is this due?”
- “How much progress is done?”
- “Can this deadline move?”
- “What happens if this slips?”
- “Is this deep work or shallow work?”

---

## 9. Calendar Design

## 9.1 Calendar View

Support:

- day view,
- week view,
- Google events,
- ChronOS focus blocks,
- free windows,
- risk overlay.

## 9.2 Calendar Block Types

- Deep Work
- Shallow Work
- Admin
- Event
- Buffer
- Rescue Block
- Feedback Gate
- Reflection

## 9.3 Calendar Write Approval

Before writing:

- show title,
- start/end,
- reason,
- affected commitment,
- edit option,
- approve button.

---

## 10. Rescue Mode Design

## 10.1 Trigger

Rescue Mode appears when:

- risk is Critical or Rescue Required,
- user manually activates,
- remaining effort exceeds safe capacity.

## 10.2 Rescue Screen

Sections:

- Crisis Summary
- Minimum Viable Completion Path
- Must Do
- Skip
- Quality Risks
- 30/60/90-Minute Sprint
- Final Checklist
- Renegotiation Option

## 10.3 Tone

Urgent but not panic-inducing.

Use:

- “Here is the viable path.”
- “This is what to cut.”
- “This must be done first.”
- “This deadline is recoverable only with scope reduction.”

Avoid:

- “You failed.”
- “Impossible.”
- “Emergency!!!”

---

## 11. Reflection Design

## 11.1 Daily Reflection

Show:

- planned vs actual,
- completed commitments,
- missed blocks,
- overrun patterns,
- tomorrow’s adjustments,
- learned user pattern.

## 11.2 Block Reflection

After focus block:

- Finished?
- Actual duration?
- Energy level?
- Blockers?
- Quality confidence?
- Notes?

## 11.3 Memory Update UI

Example:

“ChronOS learned: Coding tasks are taking 1.6× your estimates. Add debugging buffer automatically?”

Options:

- Accept
- Ignore once
- Do not learn this

---

## 12. Motion and Interaction

## 12.1 Motion Principles

Motion should show intelligence, not decoration.

Use animation for:

- time spine recalculation,
- risk transition,
- agent action progress,
- calendar block movement,
- rescue activation,
- drift detection.

Avoid:

- random floating cards,
- slow transitions,
- excessive parallax,
- decorative loops.

## 12.2 Microinteractions

- Risk node softly pulses when changed.
- Time spine redraws after replan.
- Agent trace steps appear sequentially.
- Calendar block slides after approval.
- Rescue Mode changes border tone.
- Decision Dock rises when action required.

---

## 13. Component Library

Core components:

- `ChronosLogo`
- `OvalNavbar`
- `TimeHealthBadge`
- `RiskBadge`
- `CommitmentCard`
- `TimeSpine`
- `SpineNode`
- `ActiveMissionCard`
- `NextActionStrip`
- `AgentTracePanel`
- `DriftEventCard`
- `DecisionDock`
- `CalendarBlock`
- `RescuePlanCard`
- `ReflectionCard`
- `ActionContract`
- `FeedbackGate`
- `EnergySelector`
- `AutonomyLevelControl`

Every component must support:

- loading state,
- empty state,
- error state,
- interactive state,
- accessible labels.

---

## 14. Responsive Design

### Desktop

Full Command Canvas with all zones.

### Tablet

Two-column layout:

- Time Spine + Active Console
- Agent Console collapsible

### Mobile

Stacked flow:

1. Active Mission
2. Risk Summary
3. Time Spine
4. Drift Radar
5. Decisions
6. Agent Console

Do not force full canvas complexity onto mobile.

---

## 15. Accessibility

Requirements:

- strong text contrast,
- no color-only risk indication,
- keyboard navigation,
- visible focus ring,
- semantic headings,
- reduced motion option,
- screen-reader labels for timeline nodes.

---

## 16. Empty States

### No commitments

“ChronOS needs something to operate on. Dump your next messy week here.”

### Calendar not connected

“Connect Google Calendar so ChronOS can plan around real time, not imaginary availability.”

### No drift

“No drift detected. Your current plan still holds.”

### No rescue tasks

“No critical commitments right now. Keep the spine stable.”

---

## 17. Design QA Checklist

Before accepting any page, ask:

- Does it feel like an OS, not a task list?
- Is the current action obvious?
- Is agentic behavior visible?
- Is calendar context visible where relevant?
- Is risk explainable?
- Is there too much card/table clutter?
- Are warm colors consistent?
- Is urgency calm rather than alarming?
- Does the interaction feel premium?
- Would a frontend engineer judge remember it?

---

## 18. AI Design Tool Prompt Rules

When prompting design agents, include:

- warm light theme,
- command-center layout,
- interactive time spine,
- premium SaaS quality,
- visible agentic intelligence,
- calm urgency,
- minimal clutter,
- high contrast warm text,
- dynamic but restrained motion,
- no generic dashboard appearance.

Forbid:

- cold blue enterprise dashboard,
- basic task table,
- generic chatbot panel,
- dark cyberpunk UI,
- cluttered Kanban board,
- cartoon productivity graphics,
- random gradients.

---

## 19. Signature UX Moment

The user logs:

> “API integration took 75 minutes longer than planned.”

ChronOS should visibly:

1. recalculate risk,
2. redraw the Time Spine,
3. move low-priority work,
4. preserve hard deadlines,
5. propose a Google Calendar update,
6. explain the tradeoff,
7. ask for approval.

This is the core ChronOS experience.
