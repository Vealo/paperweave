import { requestApi } from "./projects";

export interface EvidenceLink {
  id: string; claim_id: string; claim_version: number; passage_id: string; passage_file_id: string; version: number;
  passage_page: number | null; passage_text: string | null; source_title: string; relation: "supports" | "contradicts" | "contextualizes";
  rationale: string | null; review_state: "unreviewed" | "verified" | "rejected" | "needs_review" | "retracted";
  manuscript_version: number; reviewer_id: string | null; decision: string | null; decided_at: string | null; note: string | null;
}
export interface Claim { id: string; manuscript_id: string; block_position: number; text: string; version: number; manuscript_version: number; links: EvidenceLink[] }
export const listClaims = (projectId: string) => requestApi<Claim[]>(`/projects/${projectId}/claims`);
export const createClaim = (projectId: string, text: string, blockPosition: number) => requestApi<Claim>(`/projects/${projectId}/claims`, { method: "POST", body: JSON.stringify({ text, block_position: blockPosition }) });
export const addEvidenceLink = (projectId: string, claimId: string, passageId: string, relation: EvidenceLink["relation"]) =>
  requestApi<EvidenceLink>(`/projects/${projectId}/claims/${claimId}/links`, { method: "POST", body: JSON.stringify({ passage_id: passageId, relation }) });
export const retractEvidenceLink = (projectId: string, linkId: string) =>
  requestApi<EvidenceLink>(`/projects/${projectId}/claims/links/${linkId}`, { method: "DELETE" });
export const reviewEvidenceLink = (projectId: string, linkId: string, decision: "verified" | "rejected") =>
  requestApi<EvidenceLink>(`/projects/${projectId}/claims/links/${linkId}/review`, { method: "POST", body: JSON.stringify({ decision }) });
