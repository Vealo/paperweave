import { requestApi } from "./projects";
import type { Manuscript } from "./manuscript";

export interface AIProposal {
  id: string;
  project_id: string;
  manuscript_id: string;
  target_version: number;
  target_position: number;
  context_manifest: {
    target_position: number;
    selected_text: string;
    instruction: string;
    target_version: number;
  };
  suggestion: string | null;
  provider: string;
  model: string;
  status: "pending" | "accepted" | "rejected" | "stale" | "failed";
  reviewer_id: string | null;
  decision_at: string | null;
  decision_note: string | null;
  created_at: string;
  updated_at: string;
  error_code: string | null;
  manuscript: Manuscript | null;
}

export function createAIProposal(projectId: string, input: {
  expected_version: number;
  target_position: number;
  selected_text: string;
  instruction: string;
  idempotency_key: string;
}): Promise<AIProposal> {
  return requestApi<AIProposal>(`/projects/${encodeURIComponent(projectId)}/ai-proposals`, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function decideAIProposal(projectId: string, proposalId: string,
                                 decision: "accepted" | "rejected"): Promise<AIProposal> {
  return requestApi<AIProposal>(`/projects/${encodeURIComponent(projectId)}/ai-proposals/${encodeURIComponent(proposalId)}/decision`, {
    method: "POST",
    body: JSON.stringify({ decision }),
  });
}
