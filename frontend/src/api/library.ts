import { ApiError } from "./projects";

export interface SourceFile { id: string; version: number; original_name: string; media_type: string; size_bytes: number; sha256: string; created_at: string }
export interface ExtractionRun { id: string; file_id: string; processor: string; processor_version: string; status: "running" | "complete" | "empty" | "partial" | "failed"; page_count: number; error: string | null; created_at: string; completed_at: string | null }
export interface SourcePassage { id: string; run_id: string; file_id: string; page_number: number; text: string; review_state: "unreviewed" | "needs_review"; created_at: string }
export interface Source { id: string; project_id: string; title: string; authors: string | null; year: number | null; doi: string | null; metadata_provenance: string; created_at: string; files: SourceFile[] }
const apiBaseUrl = window.PAPERWEAVE_CONFIG?.apiBaseUrl;
function endpoint(path: string): string {
  if (!apiBaseUrl) throw new Error("Адрес API не задан в конфигурации приложения.");
  return `${apiBaseUrl.replace(/\/$/, "")}/api/v1${path}`;
}
async function parse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = "Не удалось выполнить запрос.";
    try { const body = await response.json() as { detail?: string | { message?: string } }; if (typeof body.detail === "string") message = body.detail; else if (body.detail?.message) message = body.detail.message; } catch { /* empty error response */ }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return await response.json() as T;
}
export function listSources(projectId: string): Promise<Source[]> { return fetch(endpoint(`/projects/${encodeURIComponent(projectId)}/sources`), { credentials: "include" }).then(parse<Source[]>); }
export function createSource(projectId: string, input: { title: string; authors?: string; year?: number; doi?: string }): Promise<Source> {
  return fetch(endpoint(`/projects/${encodeURIComponent(projectId)}/sources`), { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) }).then(parse<Source>);
}
export function uploadSourceFile(projectId: string, sourceId: string, file: File): Promise<SourceFile> {
  const form = new FormData(); form.append("file", file);
  return fetch(endpoint(`/projects/${encodeURIComponent(projectId)}/sources/${encodeURIComponent(sourceId)}/files`), { method: "POST", credentials: "include", body: form }).then(parse<SourceFile>);
}
export async function downloadSourceFile(projectId: string, sourceId: string, fileId: string): Promise<void> {
  const response = await fetch(endpoint(`/projects/${encodeURIComponent(projectId)}/sources/${encodeURIComponent(sourceId)}/files/${encodeURIComponent(fileId)}`), { credentials: "include" });
  if (!response.ok) await parse<void>(response);
  const blob = await response.blob(); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = "source.pdf"; link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 0);
}
export function deleteSourceFile(projectId: string, sourceId: string, fileId: string): Promise<void> {
  return fetch(endpoint(`/projects/${encodeURIComponent(projectId)}/sources/${encodeURIComponent(sourceId)}/files/${encodeURIComponent(fileId)}?confirmed=true`), { method: "DELETE", credentials: "include" }).then(parse<void>);
}
function fileEndpoint(projectId: string, sourceId: string, fileId: string): string {
  return `/projects/${encodeURIComponent(projectId)}/sources/${encodeURIComponent(sourceId)}/files/${encodeURIComponent(fileId)}`;
}
export function extractSourceFile(projectId: string, sourceId: string, fileId: string): Promise<ExtractionRun> {
  return fetch(endpoint(`${fileEndpoint(projectId, sourceId, fileId)}/extractions`), { method: "POST", credentials: "include" }).then(parse<ExtractionRun>);
}
export function listExtractions(projectId: string, sourceId: string, fileId: string): Promise<ExtractionRun[]> {
  return fetch(endpoint(`${fileEndpoint(projectId, sourceId, fileId)}/extractions`), { credentials: "include" }).then(parse<ExtractionRun[]>);
}
export function listPassages(projectId: string, sourceId: string, fileId: string): Promise<SourcePassage[]> {
  return fetch(endpoint(`${fileEndpoint(projectId, sourceId, fileId)}/passages`), { credentials: "include" }).then(parse<SourcePassage[]>);
}
