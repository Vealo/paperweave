import assert from "node:assert/strict";
import test from "node:test";

import {
  createAccountWithAvatar,
  retryCreatedUserAvatar,
} from "../src/views/user-creation-flow.mjs";

const user = { id: "user-123", email: "member@example.test" };
const avatarFile = { name: "avatar.png" };
const input = { display_name: "Member", email: user.email, password: "temporary-password" };

test("account creation without an avatar does not call avatar upload", async () => {
  let createCalls = 0;
  let uploadCalls = 0;

  const result = await createAccountWithAvatar({
    input,
    avatarFile: null,
    createUser: async () => { createCalls += 1; return user; },
    uploadUserAvatar: async () => { uploadCalls += 1; return user; },
  });

  assert.equal(result.status, "created_without_avatar");
  assert.equal(result.user.id, user.id);
  assert.equal(createCalls, 1);
  assert.equal(uploadCalls, 0);
});

test("avatar upload succeeds after account creation", async () => {
  const calls = [];
  const result = await createAccountWithAvatar({
    input,
    avatarFile,
    createUser: async (value) => { calls.push(["create", value]); return user; },
    uploadUserAvatar: async (id, file) => { calls.push(["upload", id, file]); return user; },
  });

  assert.equal(result.status, "created_with_avatar");
  assert.deepEqual(calls, [["create", input], ["upload", user.id, avatarFile]]);
});

test("failed upload reports the created ID and retry uploads that ID without creating another user", async () => {
  let createCalls = 0;
  const uploadIds = [];
  const createResult = await createAccountWithAvatar({
    input,
    avatarFile,
    createUser: async () => { createCalls += 1; return user; },
    uploadUserAvatar: async (id) => {
      uploadIds.push(id);
      throw new Error("temporary upload failure");
    },
  });

  assert.equal(createResult.status, "created_avatar_failed");
  assert.equal(createResult.user.id, user.id);
  assert.match(createResult.error.message, /temporary upload failure/);

  const retry = await retryCreatedUserAvatar({
    user: createResult.user,
    avatarFile,
    uploadUserAvatar: async (id) => { uploadIds.push(id); return user; },
  });

  assert.deepEqual(retry, { status: "uploaded" });
  assert.equal(createCalls, 1);
  assert.deepEqual(uploadIds, [user.id, user.id]);
});

test("account creation error rejects and never tries to upload an avatar", async () => {
  let uploadCalls = 0;

  await assert.rejects(createAccountWithAvatar({
    input,
    avatarFile,
    createUser: async () => { throw new Error("account creation failed"); },
    uploadUserAvatar: async () => { uploadCalls += 1; return user; },
  }), /account creation failed/);

  assert.equal(uploadCalls, 0);
});
