<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Message from "primevue/message";

import { deactivateUser, listUsers, updateUser, type User } from "../api/auth";
import ProfileIdentity from "../components/ProfileIdentity.vue";

interface UserDraft extends User {
  editedName: string;
  editedEmail: string;
  busy: boolean;
  error: string;
}

const router = useRouter();
const users = ref<UserDraft[]>([]);
const loading = ref(false);
const pageError = ref("");
const selectedUser = ref<UserDraft | null>(null);
const confirmVisible = ref(false);

async function refresh(): Promise<void> {
  loading.value = true;
  pageError.value = "";
  try {
    users.value = (await listUsers()).map((user) => ({
      ...user,
      editedName: user.display_name,
      editedEmail: user.email,
      busy: false,
      error: "",
    }));
  } catch (cause) {
    pageError.value = cause instanceof Error ? cause.message : "Не удалось загрузить пользователей.";
  } finally {
    loading.value = false;
  }
}

onMounted(refresh);

async function save(user: UserDraft): Promise<void> {
  user.busy = true;
  user.error = "";
  try {
    const saved = await updateUser(user.id, { display_name: user.editedName.trim(), email: user.editedEmail.trim() });
    Object.assign(user, { ...saved, editedName: saved.display_name, editedEmail: saved.email });
  } catch (cause) {
    user.error = cause instanceof Error ? cause.message : "Не удалось сохранить пользователя.";
  } finally {
    user.busy = false;
  }
}

async function toggleActive(user: UserDraft): Promise<void> {
  user.busy = true;
  user.error = "";
  try {
    const saved = user.is_active
      ? await deactivateUser(user.id)
      : await updateUser(user.id, { is_active: true });
    Object.assign(user, saved);
    confirmVisible.value = false;
  } catch (cause) {
    user.error = cause instanceof Error ? cause.message : "Не удалось изменить доступ пользователя.";
  } finally {
    user.busy = false;
  }
}

function askToggle(user: UserDraft): void {
  selectedUser.value = user;
  confirmVisible.value = true;
}
</script>

<template>
  <section class="users-management">
    <header class="page-heading page-heading--actions">
      <div>
        <p class="eyebrow">УПРАВЛЕНИЕ ДОСТУПОМ</p>
        <h1>Пользователи</h1>
        <p>Учётные записи и доступ к PaperWeave.</p>
      </div>
      <div class="page-heading__actions">
        <Button label="Обновить" severity="secondary" outlined :loading="loading" @click="refresh" />
        <Button label="Добавить пользователя" @click="router.push({ name: 'users-new' })" />
      </div>
    </header>

    <Message v-if="pageError" severity="error" :closable="false">{{ pageError }}</Message>
    <div v-else class="users-management__grid">
      <Card v-for="user in users" :key="user.id" class="user-management-card">
        <template #content>
          <div class="user-management-card__identity">
            <ProfileIdentity :display-name="user.display_name" :email="user.email" :avatar-url="user.avatar_url" />
            <span class="status-pill" :class="user.is_active ? 'status-pill--active' : 'status-pill--inactive'">
              {{ user.is_active ? 'Активен' : 'Отключён' }}
            </span>
          </div>
          <div class="auth-form">
            <div class="field">
              <label :for="`user-name-${user.id}`">Имя</label>
              <InputText :id="`user-name-${user.id}`" v-model="user.editedName" maxlength="120" fluid :disabled="user.busy || user.role === 'owner'" />
            </div>
            <div class="field">
              <label :for="`user-email-${user.id}`">Электронная почта</label>
              <InputText :id="`user-email-${user.id}`" v-model="user.editedEmail" type="email" maxlength="320" fluid :disabled="user.busy || user.role === 'owner'" />
            </div>
            <Message v-if="user.error" severity="error" :closable="false">{{ user.error }}</Message>
            <div class="user-management-card__actions">
              <Button v-if="user.role === 'member'" label="Сохранить" :loading="user.busy" :disabled="user.busy" @click="save(user)" />
              <Button v-if="user.role === 'member'"
                :label="user.is_active ? 'Отключить доступ' : 'Восстановить доступ'"
                :severity="user.is_active ? 'danger' : 'secondary'"
                :outlined="!user.is_active"
                :disabled="user.busy"
                @click="askToggle(user)"
              />
            </div>
          </div>
        </template>
      </Card>
      <Card v-if="!loading && users.length === 0">
        <template #content><p>Пока нет пользователей.</p></template>
      </Card>
    </div>

    <Dialog v-model:visible="confirmVisible" modal :header="selectedUser?.is_active ? 'Отключить доступ' : 'Восстановить доступ'" class="pw-modal-fullscreen">
      <p v-if="selectedUser?.is_active">
        Аккаунт {{ selectedUser?.display_name }} перестанет входить в систему. Все сессии будут отозваны; проекты и файлы сохранятся.
      </p>
      <p v-else>Аккаунт {{ selectedUser?.display_name }} снова сможет войти в систему.</p>
      <template #footer>
        <Button label="Отмена" severity="secondary" outlined @click="confirmVisible = false" />
        <Button :label="selectedUser?.is_active ? 'Отключить' : 'Восстановить'" :severity="selectedUser?.is_active ? 'danger' : 'primary'" :loading="selectedUser?.busy" @click="selectedUser && toggleActive(selectedUser)" />
      </template>
    </Dialog>
  </section>
</template>
