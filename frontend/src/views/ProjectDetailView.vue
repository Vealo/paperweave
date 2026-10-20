<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import Dialog from "primevue/dialog";
import Menu from "primevue/menu";
import Message from "primevue/message";
import Tag from "primevue/tag";
import Skeleton from "primevue/skeleton";
import Select from "primevue/select";
import { EditorContent, useEditor } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import { Citation } from "../editor/Citation";
import ProjectLibrary from "../components/ProjectLibrary.vue";
import ClaimEvidencePanel from "../components/ClaimEvidencePanel.vue";
import AIProposalPanel from "../components/AIProposalPanel.vue";

import { getProject, type Project } from "../api/projects";
import { createManuscript, downloadManuscriptDocx, getManuscript, updateManuscript, type Manuscript } from "../api/manuscript";
import { listSources, type Source } from "../api/library";
import { formatDate } from "../utils/formatDate";

const route = useRoute();
const project = ref<Project | null>(null);
const loading = ref(true);
const error = ref("");
const manuscript = ref<Manuscript | null>(null);
const editorReady = ref(false);
const saveState = ref<"clean" | "dirty" | "saving" | "saved" | "failed">("clean");
const saveError = ref("");
const headings = ref<Array<{ id: number; level: number; text: string }>>([]);
const selectedHeading = ref<number | null>(null);
const manuscriptMissing = ref(false);
const manuscriptLoadFailed = ref(false);
const apiState = ref<"loading" | "available" | "failed">("loading");
const claimSelection = ref({ text: "", position: 0 });
const sources = ref<Source[]>([]);
const selectedSourceId = ref<string | null>(null);
const sourcesLoadError = ref("");
const exportError = ref("");
const exporting = ref(false);
let saveTimer: ReturnType<typeof setTimeout> | undefined;
let saveSequence = 0;
let projectLoadSequence = 0;
const workspaceActionsMenu = ref();
const navigationDialogVisible = ref(false);
const contextDialogVisible = ref(false);
const libraryDialogVisible = ref(false);
const evidenceDialogVisible = ref(false);
const libraryDialogMounted = ref(false);
const evidenceDialogMounted = ref(false);
const pendingHeadingPosition = ref<number | null>(null);
const pendingClaimPosition = ref<number | null>(null);

function openLibraryDialog(): void {
  libraryDialogMounted.value = true;
  libraryDialogVisible.value = true;
}

function openEvidenceDialog(): void {
  evidenceDialogMounted.value = true;
  evidenceDialogVisible.value = true;
}

const workspaceActions = [
  { label: "Навигация проекта", command: () => { navigationDialogVisible.value = true; } },
  { label: "Контекст проекта", command: () => { contextDialogVisible.value = true; } },
  { label: "Библиотека источников", command: openLibraryDialog },
  { label: "Утверждения и основания", command: openEvidenceDialog },
];

function toggleWorkspaceActions(event: Event): void {
  workspaceActionsMenu.value?.toggle(event);
}

function selectHeading(position: number): void {
  pendingHeadingPosition.value = position;
  navigationDialogVisible.value = false;
}

function finishHeadingNavigation(): void {
  const position = pendingHeadingPosition.value;
  pendingHeadingPosition.value = null;
  if (position !== null) goToHeading(position);
}

function finishClaimNavigation(): void {
  const position = pendingClaimPosition.value;
  pendingClaimPosition.value = null;
  if (position !== null) goToClaim(position);
}

function handleClaimNavigation(position: number): void {
  pendingClaimPosition.value = position;
  evidenceDialogVisible.value = false;
}

const editor = useEditor({
  extensions: [StarterKit, Citation],
  content: { type: "doc", content: [{ type: "paragraph" }] },
  editable: true,
  onUpdate: () => {
    if (!editorReady.value) return;
    refreshHeadings();
    saveState.value = "dirty";
    saveError.value = "";
    scheduleSave();
  },
  onSelectionUpdate: ({ editor: currentEditor }) => {
    claimSelection.value = { text: currentEditor.state.doc.textBetween(currentEditor.state.selection.from, currentEditor.state.selection.to, " ").trim(), position: currentEditor.state.selection.from };
  },
});

function refreshHeadings(): void {
  const currentEditor = editor.value;
  if (!currentEditor) {
    headings.value = [];
    return;
  }
  const nextHeadings: Array<{ id: number; level: number; text: string }> = [];
  currentEditor.state.doc.descendants((node, position) => {
    if (node.type.name !== "heading") return;
    const text = node.textContent.trim();
    if (text) nextHeadings.push({ id: position, level: Number(node.attrs.level) || 1, text });
  });
  headings.value = nextHeadings;
}

function goToHeading(position: number): void {
  const currentEditor = editor.value;
  if (!currentEditor) return;
  selectedHeading.value = position;
  currentEditor.chain().focus().setTextSelection(position + 1).scrollIntoView().run();
}

function goToClaim(position: number): void {
  const currentEditor = editor.value;
  if (!currentEditor) return;
  currentEditor.chain().focus().setTextSelection(Math.min(position, currentEditor.state.doc.content.size)).scrollIntoView().run();
}

function applyAIManuscript(saved: Manuscript): void {
  if (saveTimer) clearTimeout(saveTimer);
  saveSequence += 1;
  manuscript.value = saved;
  editor.value?.commands.setContent(saved.content, { emitUpdate: false });
  refreshHeadings();
  saveState.value = "saved";
  saveError.value = "";
}

function errorMessage(reason: unknown, fallback: string): string {
  if (reason instanceof SyntaxError) return fallback;
  return reason instanceof Error ? reason.message : fallback;
}

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
    apiState.value = "available";
    const latestContent = currentEditor.getJSON() as Record<string, unknown>;
    if (JSON.stringify(latestContent) !== JSON.stringify(content)) {
      saveState.value = "dirty";
      scheduleSave();
    } else {
      saveState.value = "saved";
    }
  } catch (reason) {
    if (sequence !== saveSequence) return;
    apiState.value = "failed";
    saveState.value = "failed";
    saveError.value = errorMessage(reason, "Не удалось сохранить рукопись.");
  }
}

async function loadManuscript(projectId: string, loadSequence: number): Promise<void> {
  editorReady.value = false;
  manuscript.value = null;
  manuscriptMissing.value = false;
  manuscriptLoadFailed.value = false;
  headings.value = [];
  selectedHeading.value = null;
  saveState.value = "clean";
  saveError.value = "";
  try {
    const loaded = await getManuscript(projectId);
    if (loadSequence !== projectLoadSequence) return;
    manuscript.value = loaded;
    apiState.value = "available";
    manuscriptLoadFailed.value = false;
    editor.value?.setEditable(true);
    editor.value?.commands.setContent(manuscript.value.content);
    refreshHeadings();
    saveState.value = "saved";
  } catch (reason) {
    if (loadSequence !== projectLoadSequence) return;
    if (reason instanceof Error && "status" in reason && reason.status === 404) {
      manuscriptMissing.value = true;
      manuscriptLoadFailed.value = false;
      editor.value?.setEditable(true);
      apiState.value = "available";
      editor.value?.commands.setContent({ type: "doc", content: [{ type: "paragraph" }] });
      refreshHeadings();
    } else {
      manuscriptLoadFailed.value = true;
      editor.value?.setEditable(false);
      apiState.value = "failed";
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
  apiState.value = "loading";
  project.value = null;
  sources.value = [];
  selectedSourceId.value = null;
  sourcesLoadError.value = "";
  if (saveTimer) clearTimeout(saveTimer);
  try {
    const loadedProject = await getProject(projectId);
    if (loadSequence !== projectLoadSequence) return;
    project.value = loadedProject;
    apiState.value = "available";
    try { sources.value = await listSources(projectId); }
    catch { sourcesLoadError.value = "Не удалось загрузить библиотеку источников; обновите проект перед вставкой цитат."; }
    await loadManuscript(projectId, loadSequence);
  } catch (reason) {
    if (loadSequence !== projectLoadSequence) return;
    apiState.value = "failed";
    error.value = errorMessage(reason, "Не удалось загрузить проект. Проверьте доступность API и права доступа.");
  } finally {
    if (loadSequence === projectLoadSequence) loading.value = false;
  }
}

function insertCitation(): void {
  if (!selectedSourceId.value || !editor.value) return;
  editor.value.chain().focus().insertContent({ type: "citation", attrs: { sourceId: selectedSourceId.value } }).run();
}

async function exportDocx(): Promise<void> {
  if (!project.value || saveState.value !== "saved" || !manuscript.value) return;
  exporting.value = true;
  exportError.value = "";
  try { await downloadManuscriptDocx(project.value.id); }
  catch (reason) { exportError.value = errorMessage(reason, "Не удалось экспортировать рукопись."); }
  finally { exporting.value = false; }
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

  <section v-else-if="project" class="project-workspace" aria-label="Рабочее пространство проекта">
    <section id="manuscript" class="workspace-editor-column" aria-label="Редактор рукописи">
      <div class="workspace-titlebar">
        <div>
          <p class="eyebrow">Рабочее пространство</p>
          <h2>Рукопись</h2>
        </div>
        <div class="workspace-titlebar__actions">
          <Tag v-if="saveState === 'saved'" severity="success" value="Сохранено" />
          <Tag v-else-if="saveState === 'saving'" severity="info" value="Сохраняем" />
          <Tag v-else-if="saveState === 'dirty'" severity="warn" value="Есть изменения" />
          <Tag v-else-if="saveState === 'failed'" severity="danger" value="Ошибка сохранения" />
          <Button label="Инструменты ▾" severity="secondary" outlined aria-haspopup="true" aria-controls="workspace-actions-menu" @click="toggleWorkspaceActions" />
          <Menu id="workspace-actions-menu" ref="workspaceActionsMenu" :model="workspaceActions" popup />
        </div>
      </div>
      <Message v-if="manuscriptMissing" severity="info" :closable="false" class="workspace-notice">Рукопись ещё не создана. Начните писать — первый текст сохранится автоматически.</Message>
      <Message v-if="manuscriptLoadFailed" severity="error" :closable="false" class="workspace-notice">
        Не удалось загрузить рукопись. Редактирование временно отключено, чтобы не заменить несинхронизированную версию.
        <Button label="Повторить загрузку" severity="danger" text @click="void loadManuscript(project.id, projectLoadSequence)" />
      </Message>
      <div class="manuscript-toolbar" aria-label="Форматирование текста">
        <Button label="Жирный" severity="secondary" outlined size="small" :disabled="!editor" @click="editor?.chain().focus().toggleBold().run()" />
        <Button label="Курсив" severity="secondary" outlined size="small" :disabled="!editor" @click="editor?.chain().focus().toggleItalic().run()" />
        <Button label="Заголовок" severity="secondary" outlined size="small" :disabled="!editor" @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()" />
        <Button label="Список" severity="secondary" outlined size="small" :disabled="!editor" @click="editor?.chain().focus().toggleBulletList().run()" />
        <Select v-model="selectedSourceId" :options="sources" option-label="title" option-value="id" placeholder="Источник для цитаты" aria-label="Источник для цитаты" size="small" />
        <Button label="Вставить цитату" severity="secondary" outlined size="small" :disabled="!editor || !selectedSourceId" @click="insertCitation" />
        <Button label="Экспорт DOCX" severity="primary" size="small" :loading="exporting" :disabled="saveState !== 'saved' || !manuscript" @click="void exportDocx()" />
      </div>
      <Message v-if="sourcesLoadError" severity="warn" :closable="false" class="workspace-notice">{{ sourcesLoadError }}</Message>
      <Message v-if="exportError" severity="error" :closable="false" class="workspace-notice">{{ exportError }}</Message>
      <EditorContent v-if="editor" :editor="editor" class="manuscript-editor" />
      <Message v-if="saveState === 'failed'" severity="error" :closable="false" class="manuscript-error">
        <div class="manuscript-error__content"><span>{{ saveError }}</span><Button label="Повторить сохранение" severity="danger" text @click="void saveManuscript()" /></div>
      </Message>
    </section>

  </section>

  <Dialog v-if="project" v-model:visible="navigationDialogVisible" modal header="Навигация проекта" class="pw-modal-fullscreen workspace-dialog workspace-dialog--navigation" @after-hide="finishHeadingNavigation">
    <div class="workspace-dialog__body">
      <section class="workspace-dialog__project-summary"><p class="eyebrow">Проект</p><h2>{{ project.name }}</h2><p>{{ project.description || "Описание пока не добавлено." }}</p></section>
      <div class="workspace-nav-group"><h3>Материалы</h3><Button label="Рукопись" severity="primary" text class="workspace-nav-link workspace-nav-link--active" @click="navigationDialogVisible = false" /></div>
      <div class="workspace-nav-group"><h3>В этой рукописи</h3>
        <p v-if="!editorReady" class="workspace-muted">Загружаем структуру…</p>
        <p v-else-if="headings.length === 0" class="workspace-muted">Добавьте заголовки, чтобы создать навигацию по разделам.</p>
        <nav v-else class="outline-list" aria-label="Разделы рукописи"><Button v-for="heading in headings" :key="heading.id" :label="heading.text" severity="secondary" text class="outline-link" :class="{ 'outline-link--nested': heading.level > 2, 'outline-link--selected': selectedHeading === heading.id }" @click="selectHeading(heading.id)" /></nav>
      </div>
    </div>
  </Dialog>

  <Dialog v-if="project" v-model:visible="contextDialogVisible" modal header="Контекст проекта" class="pw-modal-fullscreen workspace-dialog workspace-dialog--context">
    <div class="workspace-dialog__body">
      <section class="context-card"><h2>Проект</h2><p>{{ project.description || "Описание пока не добавлено." }}</p><dl><dt>Создан</dt><dd>{{ formatDate(project.created_at) }}</dd><dt>ID</dt><dd><code>{{ project.id }}</code></dd></dl></section>
      <section class="context-card"><h2>Состояние</h2>
        <div class="context-status"><span>API</span><Tag :severity="apiState === 'failed' ? 'danger' : apiState === 'loading' ? 'info' : 'success'" :value="apiState === 'failed' ? 'Ошибка' : apiState === 'loading' ? 'Загрузка' : 'Доступно'" /></div>
        <div class="context-status"><span>Рукопись</span><Tag :severity="manuscriptLoadFailed || saveState === 'failed' ? 'danger' : saveState === 'saving' || saveState === 'dirty' ? 'warn' : 'success'" :value="manuscriptLoadFailed ? 'Ошибка загрузки' : saveState === 'failed' ? 'Ошибка сохранения' : saveState === 'saving' ? 'Сохранение' : saveState === 'dirty' ? 'Не сохранено' : manuscript ? `Версия ${manuscript.version}` : 'Новая'" /></div>
        <div class="context-status"><span>AI</span><Tag severity="warn" value="Только mock" /></div>
        <p class="context-hint">Mock-предложение доступно для выделенного текста сохранённой рукописи; внешней передачи нет.</p>
      </section>
      <AIProposalPanel :project-id="project.id" :selected-text="claimSelection.text" :target-position="claimSelection.position" :manuscript-version="manuscript?.version ?? null" :disabled="saveState !== 'saved' || !manuscript" @applied="applyAIManuscript" />
    </div>
  </Dialog>

  <Dialog v-if="project" v-model:visible="libraryDialogVisible" modal header="Библиотека источников" class="pw-modal-fullscreen workspace-dialog workspace-dialog--library">
    <ProjectLibrary v-if="libraryDialogMounted" :project-id="project.id" />
  </Dialog>

  <Dialog v-if="project" v-model:visible="evidenceDialogVisible" modal header="Утверждения и основания" class="pw-modal-fullscreen workspace-dialog workspace-dialog--evidence" @after-hide="finishClaimNavigation">
    <ClaimEvidencePanel v-if="evidenceDialogMounted" :project-id="project.id" :selected-text="claimSelection.text" :block-position="claimSelection.position" :disabled="saveState !== 'saved'" @navigate="handleClaimNavigation" />
  </Dialog>
</template>

<style scoped>
.project-workspace {
  display: block;
}

.workspace-muted,
.context-card p,
.context-hint {
  margin: 0;
  color: var(--p-text-muted-color);
  font-size: 0.84rem;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.workspace-nav-group {
  display: grid;
  gap: 9px;
}

.workspace-nav-group h3,
.context-card h2 {
  margin: 0;
  font-size: 0.9rem;
}

.workspace-nav-link.p-button {
  justify-content: flex-start;
}

.workspace-nav-link--active {
  background: var(--p-primary-50);
}

.outline-list {
  display: grid;
  justify-items: stretch;
  gap: 2px;
}

.outline-link.p-button {
  justify-content: flex-start;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  padding: 7px 9px;
  color: var(--p-text-color);
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.outline-link--nested.p-button {
  padding-left: 20px;
}

.outline-link--selected.p-button {
  background: var(--p-highlight-background);
  color: var(--p-highlight-color);
}

.workspace-editor-column {
  min-width: 0;
  padding: 22px;
  border: 1px solid var(--p-content-border-color);
  border-radius: var(--p-content-border-radius);
  background: var(--p-surface-50);
}

.workspace-titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
}

.workspace-titlebar__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.workspace-titlebar .eyebrow {
  margin-bottom: 7px;
}

.workspace-titlebar h2 {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  font-size: 1.55rem;
  font-weight: 500;
}

.workspace-notice {
  margin: 0 0 14px;
}

.workspace-editor-column .manuscript-editor {
  min-height: 65vh;
  margin-top: 12px;
  padding: clamp(18px, 4vw, 44px);
  background: var(--p-surface-0);
}

.workspace-editor-column :deep(.manuscript-editor .tiptap) {
  min-height: 58vh;
}

.context-card {
  display: grid;
  gap: 18px;
  padding-top: 16px;
  border-top: 1px solid var(--p-content-border-color);
}

.workspace-dialog__body {
  display: grid;
  gap: 20px;
  align-content: start;
  min-height: 100%;
  padding: 2px;
}

.workspace-dialog__project-summary {
  display: grid;
  gap: 10px;
}

.workspace-dialog__project-summary h2,
.workspace-dialog__project-summary p {
  margin: 0;
}

.workspace-dialog__project-summary p:last-child {
  color: var(--p-text-muted-color);
  line-height: 1.55;
}

.workspace-dialog :deep(.library-panel),
.workspace-dialog :deep(.evidence-panel) {
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
}

.context-card p {
  margin: 0;
}

.context-card dl {
  display: grid;
  grid-template-columns: 1fr;
  gap: 5px;
  margin: 0;
  font-size: 0.8rem;
}

.context-card dt {
  color: var(--p-text-muted-color);
}

.context-card dd {
  margin: 0 0 8px;
  overflow-wrap: anywhere;
}

.context-status {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 0.85rem;
}

.context-card .context-hint {
  margin: 0;
  font-size: 0.78rem;
}

@media (max-width: 760px) {
  .workspace-editor-column .manuscript-editor {
    min-height: 50vh;
  }

  .workspace-editor-column :deep(.manuscript-editor .tiptap) {
    min-height: 44vh;
  }
}

@media (max-width: 480px) {
  .workspace-editor-column {
    padding: 15px;
  }

  .workspace-titlebar {
    align-items: flex-start;
  }

  .workspace-titlebar__actions {
    align-items: flex-end;
    flex-direction: column-reverse;
  }
}
</style>
