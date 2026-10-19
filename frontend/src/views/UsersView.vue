<script setup lang="ts">
import { ref } from "vue";
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Password from "primevue/password";

import { ApiError } from "../api/projects";
import { createUser } from "../api/auth";

const displayName = ref("");
const email = ref("");
const password = ref("");
const error = ref("");
const success = ref("");
const busy = ref(false);

async function submit(): Promise<void> {
  if (busy.value) return;
  busy.value = true;
  error.value = "";
  success.value = "";
  try {
    const user = await createUser({
      display_name: displayName.value,
      email: email.value,
      password: password.value,
    });
    success.value = "Создана учётная запись " + user.email + ".";
    displayName.value = "";
    email.value = "";
    password.value = "";
  } catch (cause) {
    error.value = cause instanceof ApiError && cause.status === 409
      ? "Пользователь с таким адресом уже существует."
      : cause instanceof Error ? cause.message : "Не удалось создать пользователя.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section class="auth-page">
    <Card class="auth-card">
      <template #title>Добавить пользователя</template>
      <template #subtitle>Создать локальную учётную запись может только владелец.</template>
      <template #content>
        <form class="auth-form" @submit.prevent="submit">
          <div class="field">
            <label for="member-name">Имя</label>
            <InputText id="member-name" v-model="displayName" required maxlength="120" fluid :disabled="busy" />
          </div>
          <div class="field">
            <label for="member-email">Электронная почта</label>
            <InputText id="member-email" v-model="email" type="email" required maxlength="320" fluid :disabled="busy" />
          </div>
          <div class="field">
            <label for="member-password">Временный пароль</label>
            <Password id="member-password" v-model="password" :feedback="false" minlength="12" required fluid :disabled="busy" />
            <span class="field-hint">Не менее 12 символов. Передайте пароль пользователю отдельно.</span>
          </div>
          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
          <Message v-if="success" severity="success" :closable="false">{{ success }}</Message>
          <Button type="submit" label="Создать пользователя" :loading="busy" :disabled="busy" />
        </form>
      </template>
    </Card>
  </section>
</template>
