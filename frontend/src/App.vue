<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";
import Button from "primevue/button";
import Dialog from "primevue/dialog";
import Menu from "primevue/menu";

import { currentUser, getUserSettings, logout, uploadProfileAvatar } from "./api/auth";
import AppHeaderActions, { type AppHeaderAction } from "./components/AppHeaderActions.vue";
import ProfileAvatarPicker from "./components/ProfileAvatarPicker.vue";
import ProfileIdentity from "./components/ProfileIdentity.vue";

const router = useRouter();
const route = useRoute();
const sessionNotice = ref("");
const accountMenu = ref();
const settingsDialogVisible = ref(false);
const avatarUploading = ref(false);
const avatarError = ref("");
const avatarNotice = ref("");
const activeHeaderActions = computed<AppHeaderAction[]>(() =>
  route.name === "project-detail"
    ? [{ label: "К списку проектов", to: { name: "projects" } }]
    : [],
);

const accountMenuItems = computed(() => currentUser.value ? [
  { label: currentUser.value.email, disabled: true, class: "account-menu__email" },
  { separator: true },
  { label: "Профиль", icon: "pi pi-user", command: () => void router.push({ name: "profile" }) },
  { label: "Настройки", icon: "pi pi-cog", command: () => { avatarError.value = ""; avatarNotice.value = ""; settingsDialogVisible.value = true; } },
  ...(currentUser.value.role === "owner" ? [{ label: "Пользователи", icon: "pi pi-users", command: () => void router.push({ name: "users" }) }] : []),
  { separator: true },
  { label: "Выйти", icon: "pi pi-sign-out", class: "account-menu__logout", command: () => void signOut() },
] : []);

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

function toggleAccountMenu(event: Event): void {
  accountMenu.value?.toggle(event);
}

function applyTheme(theme: "system" | "light" | "dark"): void {
  const dark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("p-dark", dark);
}

async function uploadAvatar(file: File): Promise<void> {
  avatarUploading.value = true;
  avatarError.value = "";
  avatarNotice.value = "";
  try {
    await uploadProfileAvatar(file);
    avatarNotice.value = "Аватар обновлён.";
  } catch (reason) {
    avatarError.value = reason instanceof Error ? reason.message : "Не удалось загрузить аватар.";
  } finally {
    avatarUploading.value = false;
  }
}

onMounted(() => {
  window.addEventListener("paperweave:session-expired", onSessionExpired);
  void getUserSettings().then((settings) => applyTheme(settings.theme)).catch(() => undefined);
});
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
        <AppHeaderActions :actions="activeHeaderActions" />
        <div class="app-header__account">
          <Button class="account-trigger" severity="secondary" text aria-haspopup="true" aria-controls="account-menu" :aria-label="`Меню аккаунта: ${currentUser.display_name}`" @click="toggleAccountMenu">
            <ProfileIdentity :display-name="currentUser.display_name" :avatar-url="currentUser.avatar_url" variant="header" />
            <i class="pi pi-angle-down account-trigger__chevron" aria-hidden="true" />
          </Button>
          <Menu id="account-menu" ref="accountMenu" :model="accountMenuItems" popup />
        </div>
      </div>
    </header>
    <main class="app-main">
      <RouterView />
    </main>
    <Dialog v-model:visible="settingsDialogVisible" modal header="Настройки" class="pw-modal-fullscreen account-settings-dialog">
      <section v-if="currentUser" class="account-settings">
        <ProfileIdentity :display-name="currentUser.display_name" :email="currentUser.email" :avatar-url="currentUser.avatar_url" />
        <ProfileAvatarPicker :disabled="avatarUploading" :error="avatarError" :notice="avatarNotice" @select="uploadAvatar" @invalid="avatarError = $event" />
        <p class="account-settings__placeholder">Настройки системы появятся здесь позже.</p>
      </section>
    </Dialog>
    <div v-if="sessionNotice" class="sr-only" role="status">{{ sessionNotice }}</div>
  </div>
</template>
