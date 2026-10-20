import type { User } from "../api/auth";

export type UserCreationResult =
  | { status: "created_without_avatar"; user: User }
  | { status: "created_with_avatar"; user: User }
  | { status: "created_avatar_failed"; user: User; error: unknown };

export function createAccountWithAvatar(options: {
  input: { display_name: string; email: string; password: string };
  avatarFile: File | null;
  createUser(input: { display_name: string; email: string; password: string }): Promise<User>;
  uploadUserAvatar(userId: string, file: File): Promise<User>;
}): Promise<UserCreationResult>;

export function retryCreatedUserAvatar(options: {
  user: User;
  avatarFile: File;
  uploadUserAvatar(userId: string, file: File): Promise<User>;
}): Promise<{ status: "uploaded" } | { status: "failed"; error: unknown }>;
