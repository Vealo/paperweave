export async function createAccountWithAvatar({
  input,
  avatarFile,
  createUser,
  uploadUserAvatar,
}) {
  const user = await createUser(input);
  if (!avatarFile) return { status: "created_without_avatar", user };

  try {
    await uploadUserAvatar(user.id, avatarFile);
    return { status: "created_with_avatar", user };
  } catch (error) {
    return { status: "created_avatar_failed", user, error };
  }
}

export async function retryCreatedUserAvatar({ user, avatarFile, uploadUserAvatar }) {
  try {
    await uploadUserAvatar(user.id, avatarFile);
    return { status: "uploaded" };
  } catch (error) {
    return { status: "failed", error };
  }
}
