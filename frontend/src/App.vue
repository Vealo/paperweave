<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";
import Button from "primevue/button";

import { currentUser, logout } from "./api/auth";

const router = useRouter();
const sessionNotice = ref("");

function onSessionExpired(): void {
  sessionNotice.value = "Сессия завершилась. Войдите снова.";
  const next = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  void router.replace({ name: "login", query: { expired: "1", next } });
}

async function signOut(): Promise<void> {
  try {
    await logout();
  } catch {
    sessionNotice.value = "Не удалось подтвердить выход на сервере. Локальное состояние очищено.";
  } finally {
    await router.replace({ name: "login" });
  }
}

onMounted(() => window.addEventListener("paperweave:session-expired", onSessionExpired));
onUnmounted(() => window.removeEventListener("paperweave:session-expired", onSessionExpired));
</script>

<template>
  <div class="app-shell">
    <header v-if="currentUser" class="app-header">
      <div class="app-header__inner">
        <RouterLink class="brand" :to="{ name: 'projects' }">
          <span class="brand__mark" aria-hidden="true">P</span>
          <span class="brand__name">PaperWeave</span>
        </RouterLink>
        <div class="app-header__account">
          <span>{{ currentUser.display_name }}</span>
          <RouterLink :to="{ name: 'profile' }">Профиль</RouterLink>
          <RouterLink v-if="currentUser.role === 'owner'" :to="{ name: 'users' }">Пользователи</RouterLink>
          <Button label="Выйти" severity="secondary" text @click="signOut" />
        </div>
      </div>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
    <div v-if="sessionNotice" class="sr-only" role="status">{{ sessionNotice }}</div>
  </div>
</template>
