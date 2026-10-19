<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import { RouterLink, RouterView, useRouter } from "vue-router";
import Button from "primevue/button";

import { currentUser, logout } from "./api/auth";

const router = useRouter();
const sessionNotice = ref("");

function onSessionExpired(): void {
  sessionNotice.value = "Сессия завершилась. Войдите снова.";
  void router.push({ name: "login", query: { expired: "1" } });
}

async function signOut(): Promise<void> {
  await logout();
  await router.push({ name: "login" });
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
          <RouterLink v-if="currentUser.role === 'owner'" :to="{ name: 'users-new' }">Пользователи</RouterLink>
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
