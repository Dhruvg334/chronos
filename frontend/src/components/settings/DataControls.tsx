import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/auth-context";
import { Surface } from "../ui/primitives";
import { apiFetch, apiUrl, getApiErrorMessage } from "../../lib/api";

async function downloadExport() {
  const response = await apiFetch(apiUrl("/api/v1/operations/data/export"));
  if (!response.ok) throw new Error(await getApiErrorMessage(response, "Your export could not be prepared."));
  const data = await response.json();
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url; link.download = `chronos-export-${new Date().toISOString().slice(0, 10)}.json`; link.click();
  URL.revokeObjectURL(url);
}

export function DataControls() {
  const [confirmation, setConfirmation] = useState("");
  const [showDelete, setShowDelete] = useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { signOut } = useAuth();
  const exportMutation = useMutation({ mutationFn: downloadExport });
  const deleteMutation = useMutation({
    mutationFn: async () => {
      const response = await apiFetch(apiUrl("/api/v1/operations/data/delete-account"), {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirmation }),
      });
      if (!response.ok) throw new Error(await getApiErrorMessage(response, "Your account data could not be deleted."));
    },
    onSuccess: async () => { queryClient.clear(); await signOut(); navigate("/"); },
  });

  return <Surface className="p-6">
    <h2 className="font-semibold">Your data</h2>
    <p className="mt-2 text-sm leading-6 text-muted">Download an inspectable copy of your ChronOS data or permanently delete the account.</p>
    <div className="mt-4 flex flex-wrap gap-3">
      <button type="button" className="button-secondary" disabled={exportMutation.isPending} onClick={() => exportMutation.mutate()}>
        {exportMutation.isPending ? "Preparing…" : "Download data"}
      </button>
      <button type="button" className="button-secondary" aria-expanded={showDelete} onClick={() => setShowDelete(value => !value)}>Delete account data</button>
    </div>
    {showDelete && <div className="mt-4 rounded-lg border border-danger/40 p-4">
      <label className="label">Type DELETE MY ACCOUNT to confirm
        <input className="field mt-1" value={confirmation} onChange={event => setConfirmation(event.target.value)} autoComplete="off" />
      </label>
      <button type="button" className="button-primary mt-3" disabled={confirmation !== "DELETE MY ACCOUNT" || deleteMutation.isPending} onClick={() => deleteMutation.mutate()}>
        {deleteMutation.isPending ? "Deleting…" : "Permanently delete"}
      </button>
    </div>}
    {(exportMutation.isError || deleteMutation.isError) && <p role="alert" className="mt-3 text-sm text-danger">{(exportMutation.error || deleteMutation.error)?.message}</p>}
  </Surface>;
}
