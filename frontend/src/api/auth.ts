import { ref } from "vue";

import { ApiError, requestApi } from "./projects";

export interface User {
  id: string;
  email: string;
  display_name: string;
  role: "owner" | "member";
}

export interface AuthStatus {
  owner_exists: boolean;
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
