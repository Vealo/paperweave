<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Menu from "primevue/menu";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import Textarea from "primevue/textarea";

import { ApiError, createProject, listProjects, type Project } from "../api/projects";
import { formatDate } from "../utils/formatDate";

const projects = ref<Project[]>([]);
const loadingProjects = ref(true);
const refreshing = ref(false);
const listError = ref("");
const name = ref("");
const description = ref("");
const formError = ref("");
const submitting = ref(false);
const createDialogVisible = ref(false);
const projectActionsMenu = ref();

const projectActions = [
  {
    label: "Создать проект",
    command: () => openCreateDialog(),
  },
  {
    label: "Обновить список",
    command: () => void refreshProjects(),
  },
];

function openCreateDialog(): void {
  formError.value = "";
  createDialogVisible.value = true;
}

function toggleProjectActions(event: Event): void {
  projectActionsMenu.value?.toggle(event);
}

async function loadProjects(): Promise<void> {
  listError.value = "";
  try {
    projects.value = await listProjects();
  } catch (error) {
    listError.value = errorMessage(error, "Не удалось загрузить список проектов.");
  } finally {
    loadingProjects.value = false;
    refreshing.value = false;
  }
}

async function refreshProjects(): Promise<void> {
  if (refreshing.value) return;
  refreshing.value = true;
  await loadProjects();
}

async function submitProject(): Promise<void> {
  if (submitting.value) return;
  const trimmedName = name.value.trim();
  if (trimmedName.length < 1 || trimmedName.length > 200) {
    formError.value = "Название должно содержать от 1 до 200 символов.";
    return;
  }
  if (description.value.length > 5000) {
    formError.value = "Описание не должно превышать 5000 символов.";
    return;
  }

  submitting.value = true;
  formError.value = "";
  try {
    await createProject({
      name: trimmedName,
      description: description.value || null,
    });
    name.value = "";
    description.value = "";
    createDialogVisible.value = false;
    await loadProjects();
  } catch (error) {
    formError.value = errorMessage(error, "Не удалось создать проект.");
  } finally {
    submitting.value = false;
  }
}

function errorMessage(error: unknown, fallback: string): string {
  if (error instanceof ApiError && error.status === 422) {
    return "Проверьте название и описание проекта.";
  }
  return error instanceof Error ? error.message : fallback;
}

onMounted(() => void loadProjects());
</script>

<template>
  <section class="page-heading" aria-labelledby="page-title">
    <div>
      <p class="eyebrow">Рабочее пространство</p>
      <h1 id="page-title">Исследовательские проекты</h1>
      <p>Соберите источники, аргументы и черновики статьи вокруг одного исследования.</p>
    </div>
  </section>

  <div class="workspace-grid">
    <Card class="project-list">
      <template #title>
        <div class="project-list__header">
          <div>
            <div class="section-heading"><h2>Ваши проекты</h2></div>
            <span class="field-hint">{{ projects.length }} в рабочем пространстве</span>
          </div>
          <div class="project-list__actions">
            <Button
              label="Действия ▾"
              severity="secondary"
              outlined
              aria-haspopup="true"
              aria-controls="project-actions-menu"
              @click="toggleProjectActions"
            />
            <Menu id="project-actions-menu" ref="projectActionsMenu" :model="projectActions" popup />
          </div>
        </div>
      </template>
      <template #content>
        <Message v-if="listError" severity="error" :closable="false">
          <div>
            <p>{{ listError }}</p>
            <Button label="Повторить загрузку" severity="secondary" text @click="refreshProjects" />
          </div>
        </Message>

        <div v-else-if="loadingProjects" class="project-list__body" aria-label="Загрузка проектов">
          <Skeleton v-for="item in 3" :key="item" height="112px" border-radius="var(--p-content-border-radius)" />
        </div>

        <div v-else-if="projects.length === 0" class="empty-state">
          <strong>Пока нет проектов.</strong><br />
          Создайте первый — здесь появятся его материалы и заметки.
        </div>

        <div v-else class="project-list__body">
          <RouterLink
            v-for="project in projects"
            :key="project.id"
            class="project-card__target"
            :to="{ name: 'project-detail', params: { projectId: project.id } }"
            :aria-label="`Открыть проект ${project.name}`"
          >
            <Card class="project-card">
              <template #title>{{ project.name }}</template>
              <template #subtitle>Создан {{ formatDate(project.created_at) }}</template>
              <template #content>
                <p class="project-card__description">
                  {{ project.description || "Описание пока не добавлено." }}
                </p>
                <div class="project-card__footer">
                  <span>Рабочее пространство проекта</span>
                  <span class="project-card__open" aria-hidden="true">Открыть →</span>
                </div>
              </template>
            </Card>
          </RouterLink>
        </div>
      </template>
    </Card>
  </div>

  <Dialog
    v-model:visible="createDialogVisible"
    modal
    :closable="!submitting"
    :close-on-escape="!submitting"
    class="pw-modal-fullscreen project-create-dialog"
    header="Новый проект"
  >
    <div class="project-create-dialog__content">
      <p class="project-create-dialog__intro">Начните с рабочего названия и краткого вопроса.</p>
      <form id="create-project-form" @submit.prevent="submitProject">
        <div class="field">
          <label for="project-name">Название проекта</label>
          <InputText
            id="project-name"
            v-model="name"
            autocomplete="off"
            maxlength="200"
            required
            fluid
            autofocus
            :disabled="submitting"
            aria-describedby="project-name-hint"
          />
          <span id="project-name-hint" class="field-hint">От 1 до 200 символов.</span>
        </div>

        <div class="field">
          <label for="project-description">Исследовательский вопрос или заметка</label>
          <Textarea
            id="project-description"
            v-model="description"
            auto-resize
            maxlength="5000"
            rows="5"
            fluid
            :disabled="submitting"
            aria-describedby="project-description-hint"
          />
          <span id="project-description-hint" class="field-hint">Необязательно, до 5000 символов.</span>
        </div>

        <Message v-if="formError" severity="error" :closable="false" class="form-actions">
          {{ formError }}
        </Message>
      </form>
    </div>
    <template #footer>
      <Button label="Отмена" severity="secondary" text :disabled="submitting" @click="createDialogVisible = false" />
      <Button
        type="submit"
        form="create-project-form"
        label="Создать проект"
        :loading="submitting"
        :disabled="submitting"
      />
    </template>
  </Dialog>
</template>
