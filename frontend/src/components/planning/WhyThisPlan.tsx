import type { PlanExplanation } from "../../types/api";
import { Surface } from "../ui/primitives";

export function WhyThisPlan({ explanation }: { explanation: PlanExplanation }) {
  return (
    <Surface className="p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold">Why this plan?</h2>
        <span className="rounded-full bg-accent-soft px-3 py-1 text-xs font-semibold text-accent-strong">
          {explanation.ai_used ? "AI-assisted" : "Deterministic"}
        </span>
      </div>
      <p className="mt-3 text-sm text-muted">{explanation.next_action_reason}</p>
      <p className="mt-3 text-xs text-faint">
        Considered: {explanation.constraints_considered.join(", ")}.
      </p>
      {explanation.deferred.length > 0 && (
        <p className="mt-2 text-xs text-faint">Deferred: {explanation.deferred.join(", ")}.</p>
      )}
      <p className="mt-2 text-xs text-muted">{explanation.changed}</p>
      {explanation.requires_approval && (
        <p className="mt-3 text-xs font-medium text-accent-strong">Any plan change still requires your approval.</p>
      )}
    </Surface>
  );
}
