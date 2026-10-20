<script setup lang="ts">
import { onUnmounted, ref } from "vue";
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Password from "primevue/password";

import { ApiError } from "../api/projects";
import { createUser, uploadUserAvatar, type User } from "../api/auth";
import ProfileAvatarPicker from "../components/ProfileAvatarPicker.vue";
import ProfileIdentity from "../components/ProfileIdentity.vue";
import { createAccountWithAvatar, retryCreatedUserAvatar } from "./user-creation-flow.mjs";
import "./users-view.css";

const displayName = ref("");
const email = ref("");
const password = ref("");
const error = ref("");
const success = ref("");
const busy = ref(false);
const avatarFile = ref<File | null>(null);
const avatarPreviewUrl = ref<string | null>(null);
const createdUser = ref<User | null>(null);
const avatarPickerKey = ref(0);

function setAvatar(file: File): void {
  if (avatarPreviewUrl.value) URL.revokeObjectURL(avatarPreviewUrl.value);
  avatarFile.value = file;
  avatarPreviewUrl.value = URL.createObjectURL(file);
  error.value = "";
  success.value = "";
}

function clearAvatar(): void {
  if (avatarPreviewUrl.value) URL.revokeObjectURL(avatarPreviewUrl.value);
  avatarFile.value = null;
  avatarPreviewUrl.value = null;
}

function resetCreatedForm(): void {
  displayName.value = "";
  email.value = "";
  password.value = "";
  createdUser.value = null;
  clearAvatar();
  avatarPickerKey.value += 1;
}

onUnmounted(clearAvatar);

async function submit(): Promise<void> {
  if (busy.value || createdUser.value) return;
  busy.value = true;
  error.value = "";
  success.value = "";
  try {
    const result = await createAccountWithAvatar({
      input: {
        display_name: displayName.value,
        email: email.value,
        password: password.value,
      },
      avatarFile: avatarFile.value,
      createUser,
      uploadUserAvatar,
    });
    if (result.status === "created_avatar_failed") {
      createdUser.value = result.user;
      password.value = "";
      success.value = "Учётная запись " + result.user.email + " создана.";
      error.value = "Аватар не загружен: " + (result.error instanceof Error ? result.error.message : "ошибка загрузки") + ". Повторите загрузку ниже.";
      return;
    }
    if (result.status === "created_with_avatar") {
      success.value = "Создана учётная запись " + result.user.email + " с аватаром.";
    } else {
      success.value = "Создана учётная запись " + result.user.email + ".";
    }
    resetCreatedForm();
  } catch (cause) {
    error.value = cause instanceof ApiError && cause.status === 409
      ? "Пользователь с таким адресом уже существует."
      : cause instanceof Error ? cause.message : "Не удалось создать пользователя.";
  } finally {
    busy.value = false;
  }
}

async function uploadAvatarForCreatedUser(): Promise<void> {
  const user = createdUser.value;
  const file = avatarFile.value;
  if (!user || !file || busy.value) return;
  busy.value = true;
  error.value = "";
  success.value = "";
  try {
    const result = await retryCreatedUserAvatar({ user, avatarFile: file, uploadUserAvatar });
    if (result.status === "failed") {
      throw result.error;
    }
    success.value = "Создана учётная запись " + user.email + " с аватаром.";
    resetCreatedForm();
  } catch (cause) {
    success.value = "Учётная запись " + user.email + " создана.";
    error.value = "Аватар не загружен: " + (cause instanceof Error ? cause.message : "ошибка загрузки") + ". Повторите загрузку ниже.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section class="auth-page">
    <Card class="auth-card users-create-card">
      <template #title>
        <div class="users-create-header">
          <h1 class="users-create-header__title">Добавить пользователя</h1>
          <ProfileIdentity
            :display-name="displayName.trim() || createdUser?.display_name || 'Имя пользователя'"
            :email="email.trim() || createdUser?.email || null"
            :avatar-url="avatarPreviewUrl"
            variant="preview"
          />
        </div>
      </template>
      <template #subtitle>Создать локальную учётную запись может только владелец.</template>
      <template #content>
        <form class="auth-form" @submit.prevent="submit">
          <div class="users-avatar-field">
            <Message severity="info" :closable="false">
              {{ avatarFile ? "Выбранный аватар загрузится после создания учётной записи." : "Можно выбрать аватар; его загрузка начнётся после создания учётной записи." }}
            </Message>
            <ProfileAvatarPicker :key="avatarPickerKey" :disabled="busy" title="Аватар пользователя" @select="setAvatar" @invalid="error = $event" />
          </div>
          <section class="users-data-block" aria-labelledby="users-data-heading">
            <h2 id="users-data-heading">Данные пользователя</h2>
            <div class="field">
              <label for="member-name">Имя</label>
              <InputText id="member-name" v-model="displayName" required maxlength="120" fluid :disabled="busy || !!createdUser" />
            </div>
            <div class="field">
              <label for="member-email">Электронная почта</label>
              <InputText id="member-email" v-model="email" type="email" required maxlength="320" fluid :disabled="busy || !!createdUser" />
            </div>
            <div class="field">
              <label for="member-password">Временный пароль</label>
              <Password id="member-password" v-model="password" :feedback="false" minlength="12" required fluid :disabled="busy || !!createdUser" />
              <span class="field-hint">Не менее 12 символов. Передайте пароль пользователю отдельно.</span>
            </div>
          </section>
          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
          <Message v-if="success" severity="success" :closable="false">{{ success }}</Message>
          <Button v-if="createdUser && avatarFile" type="button" label="Повторить загрузку аватара" :loading="busy" :disabled="busy" @click="uploadAvatarForCreatedUser" />
          <Button v-else-if="!createdUser" type="submit" label="Создать пользователя" :loading="busy" :disabled="busy" />
        </form>
      </template>
    </Card>
  </section>
</template>
