<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import Message from "primevue/message";
import Skeleton from "primevue/skeleton";
import { EditorContent, useEditor } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";

import { getProject, type Project } from "../api/projects";
import { createManuscript, getManuscript, updateManuscript, type Manuscript } from "../api/manuscript";
import { formatDate } from "../utils/formatDate";

const route = useRoute();
const project = ref<Project | null>(null);
const loading = ref(true);
const error = ref("");
const manuscript = ref<Manuscript | null>(null);
const editorReady = ref(false);
const saveState = ref<"clean" | "dirty" | "saving" | "saved" | "failed">("clean");
const saveError = ref("");
let saveTimer: ReturnType<typeof setTimeout> | undefined;
let saveSequence = 0;
let projectLoadSequence = 0;

const editor = useEditor({
  extensions: [StarterKit],
  content: { type: "doc", content: [{ type: "paragraph" }] },
  editable: true,
  onUpdate: () => {
    if (!editorReady.value) return;
    saveState.value = "dirty";
    saveError.value = "";
    scheduleSave();
  },
});

function scheduleSave(): void {
  if (saveTimer) clearTimeout(saveTimer);
  saveTimer = setTimeout(() => void saveManuscript(), 800);
}

async function saveManuscript(): Promise<void> {
  const currentEditor = editor.value;
  const currentProject = project.value;
  if (!currentEditor || !currentProject || saveState.value === "saving") return;
  const sequence = ++saveSequence;
  const content = currentEditor.getJSON() as Record<string, unknown>;
  saveState.value = "saving";
  saveError.value = "";
  try {
    const saved = manuscript.value
      ? await updateManuscript(currentProject.id, content, manuscript.value.version)
      : await createManuscript(currentProject.id, content);
    if (sequence !== saveSequence) return;
    manuscript.value = saved;
    const latestContent = currentEditor.getJSON() as Record<string, unknown>;
    if (JSON.stringify(latestContent) !== JSON.stringify(content)) {
      saveState.value = "dirty";
      scheduleSave();
    } else {
      saveState.value = "saved";
    }
  } catch (reason) {
    if (sequence !== saveSequence) return;
    saveState.value = "failed";
    saveError.value = reason instanceof Error ? reason.message : "Не удалось сохранить рукопись.";
  }
}

async function loadManuscript(projectId: string, loadSequence: number): Promise<void> {
  editorReady.value = false;
  manuscript.value = null;
  saveState.value = "clean";
  saveError.value = "";
  try {
    const loaded = await getManuscript(projectId);
    if (loadSequence !== projectLoadSequence) return;
    manuscript.value = loaded;
    editor.value?.commands.setContent(manuscript.value.content);
    saveState.value = "saved";
  } catch (reason) {
    if (loadSequence !== projectLoadSequence) return;
    if (reason instanceof Error && "status" in reason && reason.status === 404) {
      editor.value?.commands.setContent({ type: "doc", content: [{ type: "paragraph" }] });
    } else {
      saveError.value = reason instanceof Error ? reason.message : "Не удалось загрузить рукопись.";
      saveState.value = "failed";
    }
  } finally {
    if (loadSequence === projectLoadSequence) editorReady.value = true;
  }
}

async function loadProject(projectId: string): Promise<void> {
  const loadSequence = ++projectLoadSequence;
  saveSequence += 1;
  loading.value = true;
  error.value = "";
  project.value = null;
  if (saveTimer) clearTimeout(saveTimer);
  try {
    const loadedProject = await getProject(projectId);
    if (loadSequence !== projectLoadSequence) return;
    project.value = loadedProject;
    await loadManuscript(projectId, loadSequence);
  } catch (reason) {
    if (loadSequence !== projectLoadSequence) return;
    error.value = reason instanceof Error ? reason.message : "Не удалось загрузить проект.";
  } finally {
    if (loadSequence === projectLoadSequence) loading.value = false;
  }
}

watch(
  () => String(route.params.projectId ?? ""),
  (projectId) => void loadProject(projectId),
  { immediate: true },
);

onBeforeUnmount(() => {
  if (saveTimer) clearTimeout(saveTimer);
  editor.value?.destroy();
});
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
      <section class="manuscript-section" aria-label="Рукопись проекта">
        <div class="manuscript-heading">
          <div>
            <h2>Рукопись</h2>
            <p>Черновик статьи, сохранённый в этом проекте.</p>
          </div>
          <div class="manuscript-save-state" role="status" aria-live="polite">
            <span v-if="saveState === 'dirty'">Есть несохранённые изменения</span>
            <span v-else-if="saveState === 'saving'">Сохраняем…</span>
            <span v-else-if="saveState === 'saved'">Сохранено<span v-if="manuscript"> · версия {{ manuscript.version }}</span></span>
            <span v-else-if="saveState === 'failed'">Ошибка сохранения</span>
          </div>
        </div>
        <div class="manuscript-toolbar" aria-label="Форматирование текста">
          <Button label="Жирный" severity="secondary" outlined size="small" :disabled="!editor" @click="editor?.chain().focus().toggleBold().run()" />
          <Button label="Курсив" severity="secondary" outlined size="small" :disabled="!editor" @click="editor?.chain().focus().toggleItalic().run()" />
          <Button label="Заголовок" severity="secondary" outlined size="small" :disabled="!editor" @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()" />
          <Button label="Список" severity="secondary" outlined size="small" :disabled="!editor" @click="editor?.chain().focus().toggleBulletList().run()" />
        </div>
        <EditorContent v-if="editor" :editor="editor" class="manuscript-editor" />
        <Message v-if="saveState === 'failed'" severity="error" :closable="false" class="manuscript-error">
          <div class="manuscript-error__content">
            <span>{{ saveError }}</span>
            <Button label="Повторить сохранение" severity="danger" text @click="void saveManuscript()" />
          </div>
        </Message>
      </section>
    </template>
  </Card>
</template>
