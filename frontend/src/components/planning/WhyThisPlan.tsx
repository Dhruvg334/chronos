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
      {explanation.detail !== "brief" && <p className="mt-3 text-xs text-faint">
        Considered: {explanation.constraints_considered.join(", ")}.
      </p>}
      {explanation.detail !== "brief" && explanation.deferred.length > 0 && (
        <p className="mt-2 text-xs text-faint">Deferred: {explanation.deferred.join(", ")}.</p>
      )}
      {explanation.detail === "detailed" && explanation.changed && <p className="mt-2 text-xs text-muted">{explanation.changed}</p>}
      {explanation.requires_approval && (
        <p className="mt-3 text-xs font-medium text-accent-strong">Any plan change still requires your approval.</p>
      )}
      {explanation.sources && explanation.sources.length > 0 && (
        <details className="mt-4 border-t border-line pt-3">
          <summary className="cursor-pointer text-sm font-medium">Sources used</summary>
          <div className="mt-3 space-y-3">
            {explanation.sources.map((source) => (
              <div key={`${source.source_id}-${source.excerpt}`} className="rounded-lg bg-surface-subtle p-3">
                <p className="text-sm font-medium">Based on {source.source_title}</p>
                <p className="mt-1 text-xs text-muted">{source.reason_selected}</p>
                <blockquote className="mt-2 border-l-2 border-accent pl-3 text-sm text-muted">{source.excerpt}</blockquote>
              </div>
            ))}
          </div>
        </details>
      )}
      {explanation.retrieval_available === false && (
        <p className="mt-3 text-xs text-muted">Document context was unavailable. This plan still uses your structured constraints.</p>
      )}
    </Surface>
  );
}
