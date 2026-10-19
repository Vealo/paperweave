<script setup lang="ts">
import { ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";

import { getProject, type Project } from "../api/projects";
import { formatDate } from "../utils/formatDate";

const route = useRoute();
const project = ref<Project | null>(null);
const loading = ref(true);
const error = ref("");

async function loadProject(projectId: string): Promise<void> {
  loading.value = true;
  error.value = "";
  project.value = null;
  try {
    project.value = await getProject(projectId);
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Не удалось загрузить проект.";
  } finally {
    loading.value = false;
  }
}

watch(
  () => String(route.params.projectId ?? ""),
  (projectId) => void loadProject(projectId),
  { immediate: true },
);
</script>

<template>
  <div class="detail-actions">
    <RouterLink to="/" custom v-slot="{ navigate }">
      <Button label="К списку проектов" severity="secondary" text @click="navigate" />
    </RouterLink>
  </div>

  <Card v-if="loading" class="detail-card" aria-label="Загрузка проекта">
    <template #content>
      <Skeleton width="55%" height="2rem" class="field" />
      <Skeleton width="80%" height="1rem" class="field" />
      <Skeleton height="120px" class="field" />
    </template>
  </Card>

  <Message v-else-if="error" severity="error" :closable="false" class="detail-card">
    <div>
      <p>{{ error }}</p>
      <RouterLink to="/" custom v-slot="{ navigate }">
        <Button label="Вернуться к списку" severity="secondary" text @click="navigate" />
      </RouterLink>
    </div>
  </Message>

  <Card v-else-if="project" class="detail-card">
    <template #title>{{ project.name }}</template>
    <template #subtitle>Исследовательский проект</template>
    <template #content>
      <p class="detail-description">
        {{ project.description || "Описание пока не добавлено." }}
      </p>
      <dl class="detail-meta">
        <dt>Идентификатор</dt>
        <dd><code>{{ project.id }}</code></dd>
        <dt>Создан</dt>
        <dd>{{ formatDate(project.created_at) }}</dd>
      </dl>
    </template>
  </Card>
</template>
