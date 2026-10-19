import { requestApi } from "./projects";

export interface Manuscript {
  id: string;
  project_id: string;
  content: Record<string, unknown>;
  version: number;
  updated_at: string;
}

export function getManuscript(projectId: string): Promise<Manuscript> {
  return requestApi<Manuscript>(`/projects/${encodeURIComponent(projectId)}/manuscript`);
}

export function createManuscript(projectId: string, content: Record<string, unknown>): Promise<Manuscript> {
  return requestApi<Manuscript>(`/projects/${encodeURIComponent(projectId)}/manuscript`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function updateManuscript(
  projectId: string,
  content: Record<string, unknown>,
  expectedVersion: number,
): Promise<Manuscript> {
  return requestApi<Manuscript>(`/projects/${encodeURIComponent(projectId)}/manuscript`, {
    method: "PUT",
    body: JSON.stringify({ content, expected_version: expectedVersion }),
  });
}


export interface ManuscriptRevision {
  version: number;
  content: Record<string, unknown>;
  created_at: string;
}

export function getManuscriptVersion(projectId: string, version: number): Promise<ManuscriptRevision> {
  return requestApi<ManuscriptRevision>(`/projects/${encodeURIComponent(projectId)}/manuscript/versions/${version}`);
}
