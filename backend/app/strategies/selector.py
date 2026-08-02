from __future__ import annotations

from app.strategies.models import StrategyContext, StrategyId, StrategyPreferences, StrategyRecommendation


class StrategySelector:
    """Return at most one primary recommendation using deterministic evidence."""

    def recommend(self, context: StrategyContext, preferences: StrategyPreferences | None = None) -> StrategyRecommendation | None:
        prefs = preferences or StrategyPreferences()

        def enabled(strategy: StrategyId) -> bool:
            return strategy in prefs.enabled

        if context.recurring and context.missed_yesterday and context.recent_completions > 0 and enabled(StrategyId.CONTINUITY):
            return StrategyRecommendation(strategy=StrategyId.CONTINUITY, title="Restart the routine gently", why="A recent miss follows an established pattern.", evidence=(f"{context.recent_completions} recent completions", "missed yesterday"), action="Do the smallest useful version today, then return to the normal cadence.", tradeoff="A smaller session advances less work today but lowers restart friction.", confidence="high")

        if context.deep_work_active and context.similar_quick_tasks >= 2 and enabled(StrategyId.BATCHING):
            return StrategyRecommendation(strategy=StrategyId.BATCHING, title="Batch the quick tasks", why="Several short tasks would repeatedly interrupt active focus.", evidence=(f"{context.similar_quick_tasks} similar tasks", "deep-work block active"), action="Collect them for one communication batch after the focus block.", tradeoff="Replies wait until the batch, preserving attention now.", confidence="high")

        if context.estimate_minutes is not None and context.estimate_minutes <= prefs.quick_task_threshold_minutes and not context.deep_work_active and enabled(StrategyId.QUICK_ACTION):
            return StrategyRecommendation(strategy=StrategyId.QUICK_ACTION, title="Complete the quick action", why="The estimate is within your quick-task threshold and no focus block is active.", evidence=(f"{context.estimate_minutes}-minute estimate", f"{prefs.quick_task_threshold_minutes}-minute threshold"), action=f"Complete: {context.task_title or 'the task'}.", tradeoff="Starting it now briefly delays the next planned item.", confidence="high", alternatives=(StrategyId.BATCHING,))

        overloaded = context.free_minutes is not None and context.remaining_work_minutes is not None and context.remaining_work_minutes > context.free_minutes
        if overloaded and context.major_outcomes >= 1 and enabled(StrategyId.CONSTRAINED_DAY):
            return StrategyRecommendation(strategy=StrategyId.CONSTRAINED_DAY, title="Constrain the day", why="The planned work does not fit the available time.", evidence=(f"{context.remaining_work_minutes} minutes planned", f"{context.free_minutes} minutes free"), action="Protect one major outcome, choose the most useful short tasks, keep essential maintenance, and defer the rest explicitly.", tradeoff="Some work must move; the recommendation favors a credible plan over nominal completeness.", confidence="high", alternatives=(StrategyId.TIME_BLOCKING,))

        if context.urgent and context.important and enabled(StrategyId.EISENHOWER):
            action = "Start now and reserve the remaining work as a protected block."
            return StrategyRecommendation(strategy=StrategyId.EISENHOWER, title="Do now", why="The work is both urgent and important.", evidence=("urgent", "important", f"deadline in {context.deadline_minutes} minutes" if context.deadline_minutes is not None else "near deadline"), action=action, tradeoff="Lower-priority work may need explicit deferral.", confidence="high", alternatives=(StrategyId.TIME_BLOCKING,))

        if context.needs_scheduling and enabled(StrategyId.TIME_BLOCKING):
            return StrategyRecommendation(strategy=StrategyId.TIME_BLOCKING, title="Reserve a realistic block", why="The work needs a specific place in the plan.", evidence=("unscheduled work", "availability required"), action="Choose a free interval, include transition time, and confirm there is no overlap.", tradeoff="A reserved block reduces flexible time elsewhere.", confidence="medium")

        if context.estimate_minutes and context.estimate_minutes >= prefs.focus_minutes and enabled(StrategyId.FOCUS_INTERVAL):
            return StrategyRecommendation(strategy=StrategyId.FOCUS_INTERVAL, title="Use a focus interval", why="The task is long enough to benefit from a protected interval.", evidence=(f"{context.estimate_minutes}-minute estimate", f"{prefs.focus_minutes}-minute preference"), action=f"Focus for {prefs.focus_minutes} minutes, then take a {prefs.break_minutes}-minute break or finish early.", tradeoff="The interval protects attention but may split work at an artificial boundary.", confidence="medium")

        # Energy-aware advice is intentionally unavailable without sufficient evidence.
        return None
