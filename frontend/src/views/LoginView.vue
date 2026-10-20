<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Password from "primevue/password";

import { ApiError } from "../api/projects";
import { getAuthStatus, login, setupOwner } from "../api/auth";

const route = useRoute();
const router = useRouter();
const setupMode = ref(false);
const name = ref("");
const email = ref("");
const password = ref("");
const error = ref("");
const busy = ref(false);
const unavailable = ref(route.query.unavailable === "1");

async function checkAuthAvailability(): Promise<void> {
  try {
    setupMode.value = !(await getAuthStatus()).owner_exists;
    unavailable.value = false;
  } catch {
    unavailable.value = true;
  }
}

onMounted(checkAuthAvailability);

async function submit(): Promise<void> {
  if (busy.value) return;
  busy.value = true;
  error.value = "";
  try {
    if (setupMode.value) {
      await setupOwner({ email: email.value, display_name: name.value, password: password.value });
    } else {
      await login({ email: email.value, password: password.value });
    }
    const next = typeof route.query.next === "string" ? route.query.next : "/";
    await router.replace(next.startsWith("/") && !next.startsWith("//") ? next : "/");
  } catch (cause) {
    if (cause instanceof ApiError && cause.status === 401) {
      error.value = "Неверный адрес почты или пароль.";
    } else if (cause instanceof ApiError && cause.status === 409) {
      error.value = "Первичная настройка уже завершена. Обновите страницу и войдите.";
      setupMode.value = false;
    } else if (cause instanceof Error) {
      error.value = cause.message;
    } else {
      error.value = "Не удалось выполнить вход.";
    }
  } finally {
    busy.value = false;
  }
}

const expired = route.query.expired === "1";
</script>

<template>
  <main class="auth-page">
    <Card class="auth-card">
      <template #title>{{ setupMode ? "Создать владельца PaperWeave" : "Войти в PaperWeave" }}</template>
      <template #subtitle>
        {{ setupMode ? "Первичная настройка доступна только один раз на этой локальной установке." : "Используйте локальную учётную запись." }}
      </template>
      <template #content>
        <Message v-if="expired" severity="warn" :closable="false">
          Сессия завершилась. Войдите снова; несохранённые изменения могли не попасть на сервер.
        </Message>
        <Message v-if="unavailable" severity="error" :closable="false">
          Не удалось проверить состояние авторизации. Проверьте доступность API.
          <Button type="button" label="Повторить проверку" severity="secondary" text @click="checkAuthAvailability" />
        </Message>
        <form class="auth-form" @submit.prevent="submit">
          <div v-if="setupMode" class="field">
            <label for="owner-name">Имя владельца</label>
            <InputText id="owner-name" v-model="name" required maxlength="120" fluid :disabled="busy" />
          </div>
          <div class="field">
            <label for="email">Электронная почта</label>
            <InputText id="email" v-model="email" type="email" autocomplete="username" required maxlength="320" fluid :disabled="busy" />
          </div>
          <div class="field">
            <label for="password">Пароль</label>
            <Password id="password" v-model="password" autocomplete="current-password" :feedback="setupMode" :minlength="12" required fluid :disabled="busy" />
            <span v-if="setupMode" class="field-hint">Не менее 12 символов.</span>
          </div>
          <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
          <Button type="submit" :label="setupMode ? 'Создать владельца' : 'Войти'" :loading="busy" :disabled="busy || unavailable" />
        </form>
      </template>
    </Card>
  </main>
</template>
