export interface Project {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
}

export interface CreateProjectInput {
  name: string;
  description: string | null;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const apiBaseUrl = window.PAPERWEAVE_CONFIG?.apiBaseUrl;

function endpoint(path: string): string {
  if (!apiBaseUrl) {
    throw new Error("Адрес API не задан в конфигурации приложения.");
  }
  return `${apiBaseUrl.replace(/\/$/, "")}/api/v1${path}`;
}

export async function requestApi<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(endpoint(path), {
      ...init,
      credentials: "include",
      headers: {
        ...(init?.body ? { "Content-Type": "application/json" } : {}),
        ...init?.headers,
      },
    });
  } catch {
    throw new Error("Не удалось связаться с API. Проверьте, что приложение запущено.");
  }

  if (!response.ok) {
    const method = (init?.method ?? "GET").toUpperCase();
    const isSessionRestore = path === "/auth/me" && method === "GET";
    if (response.status === 401 && !["/auth/login", "/auth/bootstrap", "/auth/status"].includes(path) && !isSessionRestore) {
      window.dispatchEvent(new Event("paperweave:session-expired"));
    }
    let message = "Не удалось выполнить запрос.";
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) message = body.detail;
    } catch {
      // The server may return an empty or non-JSON error response.
    }
    throw new ApiError(message, response.status);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export async function getReadiness(): Promise<boolean> {
  let response: Response;
  try {
    response = await fetch(endpoint("/health/ready"), { cache: "no-store" });
  } catch {
    throw new Error("API недоступен.");
  }
  if (response.status === 503) return false;
  if (!response.ok) throw new Error("Не удалось проверить состояние API.");
  return true;
}

export function listProjects(): Promise<Project[]> {
  return requestApi<Project[]>("/projects");
}

export function createProject(input: CreateProjectInput): Promise<Project> {
  return requestApi<Project>("/projects", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function getProject(projectId: string): Promise<Project> {
  return requestApi<Project>(`/projects/${encodeURIComponent(projectId)}`);
}

export function updateProject(projectId: string, input: CreateProjectInput): Promise<Project> {
  return requestApi<Project>("/projects/" + encodeURIComponent(projectId), {
    method: "PUT",
    body: JSON.stringify(input),
  });
}
