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

export function getAuthStatus(): Promise<AuthStatus> {
  return requestApi<AuthStatus>("/auth/status");
}

export async function getCurrentUser(): Promise<User> {
  const user = await requestApi<User>("/auth/me");
  currentUser.value = user;
  return user;
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
  currentUser.value = user;
  return user;
}

export async function login(input: { email: string; password: string }): Promise<User> {
  const user = await requestApi<User>("/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });
  currentUser.value = user;
  return user;
}

export async function logout(): Promise<void> {
  try {
    await requestApi<void>("/auth/logout", { method: "POST" });
  } finally {
    currentUser.value = null;
  }
}

export async function uploadProfileAvatar(file: File): Promise<User> {
  const formData = new FormData();
  formData.append("file", file);
  const user = await requestApiFormData<User>("/auth/me/avatar", formData);
  currentUser.value = user;
  return user;
}

export async function removeProfileAvatar(): Promise<User> {
  const user = await requestApi<User>("/auth/me/avatar", { method: "DELETE" });
  currentUser.value = user;
  return user;
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
  currentUser.value = user;
  return user;
}

export async function changePassword(input: {
  current_password: string;
  new_password: string;
}): Promise<void> {
  await requestApi<void>("/auth/me/password", {
    method: "POST",
    body: JSON.stringify(input),
  });
  currentUser.value = null;
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
