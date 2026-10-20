<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Password from "primevue/password";

import {
  changePassword,
  currentUser,
  removeProfileAvatar,
  updateProfile,
  uploadProfileAvatar,
} from "../api/auth";
import ProfileAvatarPicker from "../components/ProfileAvatarPicker.vue";
import ProfileIdentity from "../components/ProfileIdentity.vue";

const router = useRouter();
const busy = ref(false);
const avatarUploading = ref(false);
const error = ref("");
const notice = ref("");
const passwordError = ref("");
const passwordNotice = ref("");
const form = reactive({
  displayName: currentUser.value?.display_name ?? "",
  email: currentUser.value?.email ?? "",
  currentPassword: "",
  newPassword: "",
});
async function saveProfile(): Promise<void> {
  busy.value = true;
  error.value = "";
  notice.value = "";
  try {
    await updateProfile({
      display_name: form.displayName.trim(),
      email: form.email.trim(),
      ...(form.email.trim().toLowerCase() !== currentUser.value?.email.toLowerCase()
        ? { current_password: form.currentPassword }
        : {}),
    });
    form.currentPassword = "";
    notice.value = "Данные профиля сохранены.";
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : "Не удалось сохранить профиль.";
  } finally {
    busy.value = false;
  }
}

async function savePassword(): Promise<void> {
  passwordError.value = "";
  passwordNotice.value = "";
  try {
    await changePassword({ current_password: form.currentPassword, new_password: form.newPassword });
    form.currentPassword = "";
    form.newPassword = "";
    await router.replace({ name: "login", query: { expired: "1" } });
  } catch (cause) {
    passwordError.value = cause instanceof Error ? cause.message : "Не удалось изменить пароль.";
  }
}

async function uploadAvatar(file: File): Promise<void> {
  if (avatarUploading.value) return;
  avatarUploading.value = true;
  error.value = "";
  notice.value = "";
  try {
    await uploadProfileAvatar(file);
    notice.value = "Аватар обновлён.";
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : "Не удалось загрузить аватар.";
  } finally {
    avatarUploading.value = false;
  }
}

async function removeAvatar(): Promise<void> {
  try {
    currentUser.value = await removeProfileAvatar();
    notice.value = "Аватар удалён.";
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : "Не удалось удалить аватар.";
  }
}

</script>

<template>
  <section class="profile-page">
    <header class="page-heading">
      <p class="eyebrow">УЧЁТНАЯ ЗАПИСЬ</p>
      <h1>Мой профиль</h1>
      <p>Управление личными данными, фотографией профиля и безопасностью учётной записи.</p>
    </header>

    <div class="profile-page__grid">
      <Card>
        <template #title>Профиль пользователя</template>
        <template #content>
          <div class="profile-page__identity">
            <ProfileIdentity :display-name="form.displayName || 'Имя пользователя'" :email="form.email" :avatar-url="currentUser?.avatar_url ?? null" />
            <ProfileAvatarPicker :disabled="avatarUploading" :uploading="avatarUploading" :error="error" :notice="notice" @select="uploadAvatar" @invalid="error = $event" />
            <Button v-if="currentUser?.avatar_url" label="Удалить аватар" severity="secondary" text @click="removeAvatar" />
          </div>
          <form class="auth-form" @submit.prevent="saveProfile">
            <div class="field">
              <label for="profile-name">Имя</label>
            <InputText id="profile-name" v-model="form.displayName" required maxlength="120" fluid :disabled="busy || avatarUploading" autocomplete="name" />
            </div>
            <div class="field">
              <label for="profile-email">Электронная почта</label>
              <InputText id="profile-email" v-model="form.email" type="email" required maxlength="320" fluid :disabled="busy || avatarUploading" autocomplete="email" />
            </div>
            <div v-if="form.email.trim().toLowerCase() !== currentUser?.email.toLowerCase()" class="field">
              <label for="profile-current-password">Текущий пароль для смены email</label>
              <Password id="profile-current-password" v-model="form.currentPassword" :feedback="false" required fluid autocomplete="current-password" />
            </div>
            <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
            <Message v-if="notice" severity="success" :closable="false">{{ notice }}</Message>
            <Button type="submit" label="Сохранить профиль" :loading="busy" :disabled="busy || avatarUploading" />
          </form>
        </template>
      </Card>

      <Card>
        <template #title>Безопасность</template>
        <template #content>
          <form class="auth-form" @submit.prevent="savePassword">
            <div class="field">
              <label for="password-current">Текущий пароль</label>
              <Password id="password-current" v-model="form.currentPassword" :feedback="false" required fluid autocomplete="current-password" />
            </div>
            <div class="field">
              <label for="password-new">Новый пароль</label>
              <Password id="password-new" v-model="form.newPassword" :feedback="false" minlength="12" required fluid autocomplete="new-password" />
              <span class="field-hint">Не менее 12 символов. После смены пароля потребуется войти снова.</span>
            </div>
            <Message v-if="passwordError" severity="error" :closable="false">{{ passwordError }}</Message>
            <Message v-if="passwordNotice" severity="success" :closable="false">{{ passwordNotice }}</Message>
            <Button type="submit" label="Изменить пароль" />
          </form>
        </template>
      </Card>
    </div>
  </section>
</template>
