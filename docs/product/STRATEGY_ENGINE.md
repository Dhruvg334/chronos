# Strategy Engine

The Strategy Engine is a typed reasoning library, not a collection of pages.

Definitions include eligibility, evidence requirements, contraindications, explanation templates, and preferences. The selector returns zero or one primary recommendation with optional alternatives.

Implemented deterministic recommendations:

- quick action when a task fits the user threshold and no focus interval is active;
- batching for similar short tasks during protected work;
- time blocking for unscheduled work;
- Eisenhower **Do now** for urgent and important work;
- constrained-day planning when estimated work exceeds capacity;
- configurable focus intervals;
- continuity recovery after a missed repeated behavior.

Energy-aware scheduling is intentionally withheld until user-specific sample size and confidence are sufficient. The catalog also defines digital reset and the optional 8/8/8 decision lens for later selection rules.

Every recommendation explains why, evidence, action, trade-off, and automatic-change status. Current recommendations never change data automatically.
