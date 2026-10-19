import { requestApi, ApiError } from "./projects";

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

export async function downloadManuscriptDocx(projectId: string): Promise<void> {
  const apiBaseUrl = window.PAPERWEAVE_CONFIG?.apiBaseUrl;
  if (!apiBaseUrl) throw new Error("Адрес API не задан в конфигурации приложения.");
  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/projects/${encodeURIComponent(projectId)}/manuscript/export.docx`, { credentials: "include" });
  } catch {
    throw new Error("Не удалось связаться с API. Проверьте, что приложение запущено.");
  }
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event("paperweave:session-expired"));
    let message = "Не удалось экспортировать рукопись.";
    try { message = ((await response.json()) as { detail?: string }).detail ?? message; } catch { /* Non-JSON response. */ }
    throw new ApiError(message, response.status);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "paperweave-manuscript.docx";
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
