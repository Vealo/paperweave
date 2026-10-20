import { ref } from "vue";

import { ApiError, requestApi, requestApiFormData } from "./projects";

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: "owner" | "member";
  avatar_url: string | null;
  is_active: boolean;
}

export interface AuthStatus {
  owner_exists: boolean;
}

export interface UserSettings {
  user_id: string;
  theme: "system" | "light" | "dark";
}

export const currentUser = ref<User | null>(null);

export type SessionResolution =
  | { status: "authenticated"; user: User }
  | { status: "setup" }
  | { status: "anonymous" }
  | { status: "unavailable" };

let sessionResolution: SessionResolution | null = null;
let sessionRestore: Promise<SessionResolution> | null = null;
let sessionEpoch = 0;
let authStatusCache: AuthStatus | null = null;
let authStatusRestore: Promise<AuthStatus> | null = null;

function rememberUser(user: User): User {
  currentUser.value = user;
  sessionResolution = { status: "authenticated", user };
  sessionRestore = null;
  sessionEpoch += 1;
  return user;
}

function clearSession(): void {
  currentUser.value = null;
  sessionResolution = { status: "anonymous" };
  sessionRestore = null;
  sessionEpoch += 1;
}

if (typeof window !== "undefined") {
  window.addEventListener("paperweave:session-expired", clearSession);
}

export function getAuthStatus(): Promise<AuthStatus> {
  if (authStatusCache) return Promise.resolve(authStatusCache);
  if (authStatusRestore) return authStatusRestore;
  authStatusRestore = requestApi<AuthStatus>("/auth/status").then((status) => {
    authStatusCache = status;
    return status;
  }).finally(() => {
    authStatusRestore = null;
  });
  return authStatusRestore;
}

export async function getCurrentUser(): Promise<User> {
  const session = await restoreSession();
  if (session.status === "authenticated") return session.user;
  if (session.status === "anonymous") throw new ApiError("Authentication required", 401);
  if (session.status === "setup") throw new Error("Owner setup is required.");
  throw new Error("Could not restore the current session.");
}

export async function restoreSession(): Promise<SessionResolution> {
  if (currentUser.value) return { status: "authenticated", user: currentUser.value };
  if (sessionResolution) return sessionResolution;
  if (sessionRestore) return sessionRestore;

  const restoreEpoch = sessionEpoch;
  sessionRestore = (async () => {
    try {
      const authStatus = await getAuthStatus();
      if (sessionEpoch !== restoreEpoch) return sessionResolution ?? { status: "anonymous" };
      if (!authStatus.owner_exists) {
        sessionResolution = { status: "setup" };
        return sessionResolution;
      }
      try {
        const user = await requestApi<User>("/auth/me");
        if (sessionEpoch !== restoreEpoch) return sessionResolution ?? { status: "anonymous" };
        return { status: "authenticated", user: rememberUser(user) };
      } catch (error) {
        if (sessionEpoch !== restoreEpoch) return sessionResolution ?? { status: "anonymous" };
        if (isSessionError(error)) {
          sessionResolution = { status: "anonymous" };
          return sessionResolution;
        }
        throw error;
      }
    } catch {
      if (sessionEpoch !== restoreEpoch) return sessionResolution ?? { status: "anonymous" };
      // Do not cache an outage as a session state: later navigation or the
      // login screen must be able to retry once the API becomes available.
      return { status: "unavailable" };
    } finally {
      sessionRestore = null;
    }
  })();
  return sessionRestore;
}

export async function setupOwner(input: {
  email: string;
  display_name: string;
  password: string;
}): Promise<User> {
  const user = await requestApi<User>("/auth/bootstrap", {
    method: "POST",
    body: JSON.stringify(input),
  });
  authStatusCache = { owner_exists: true };
  return rememberUser(user);
}

export async function login(input: { email: string; password: string }): Promise<User> {
  const user = await requestApi<User>("/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
  authStatusCache = { owner_exists: true };
  return rememberUser(user);
}

export async function logout(): Promise<void> {
  try {
    await requestApi<void>("/auth/logout", { method: "POST" });
  } finally {
    clearSession();
  }
}

export async function uploadProfileAvatar(file: File): Promise<User> {
  const formData = new FormData();
  formData.append("file", file);
  const user = await requestApiFormData<User>("/auth/me/avatar", formData);
  return rememberUser(user);
}

export async function removeProfileAvatar(): Promise<User> {
  const user = await requestApi<User>("/auth/me/avatar", { method: "DELETE" });
  return rememberUser(user);
}

export async function updateProfile(input: {
  display_name?: string;
  email?: string;
  current_password?: string;
}): Promise<User> {
  const user = await requestApi<User>("/auth/me", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
  return rememberUser(user);
}

export async function changePassword(input: {
  current_password: string;
  new_password: string;
}): Promise<void> {
  await requestApi<void>("/auth/me/password", {
    method: "POST",
    body: JSON.stringify(input),
  });
  clearSession();
}

export function getUserSettings(): Promise<UserSettings> {
  return requestApi<UserSettings>("/auth/me/settings");
}

export function updateUserSettings(input: Pick<UserSettings, "theme">): Promise<UserSettings> {
  return requestApi<UserSettings>("/auth/me/settings", {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function listUsers(): Promise<User[]> {
  return requestApi<User[]>("/auth/users");
}

export function updateUser(userId: string, input: {
  display_name?: string;
  email?: string;
  is_active?: boolean;
}): Promise<User> {
  return requestApi<User>(`/auth/users/${encodeURIComponent(userId)}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deactivateUser(userId: string): Promise<User> {
  return requestApi<User>(`/auth/users/${encodeURIComponent(userId)}`, { method: "DELETE" });
}

export async function uploadUserAvatar(userId: string, file: File): Promise<User> {
  const formData = new FormData();
  formData.append("file", file);
  return requestApiFormData<User>(`/auth/users/${encodeURIComponent(userId)}/avatar`, formData);
}

export async function createUser(input: {
  email: string;
  display_name: string;
  password: string;
}): Promise<User> {
  return requestApi<User>("/auth/users", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function isSessionError(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401;
}
