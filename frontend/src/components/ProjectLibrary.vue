<script setup lang="ts">
import { onMounted, ref } from "vue";
import Button from "primevue/button";
import Card from "primevue/card";
import FileUpload from "primevue/fileupload";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import { createSource, deleteSourceFile, downloadSourceFile, listSources, uploadSourceFile, type Source } from "../api/library";
const props = defineProps<{ projectId: string }>();
const sources = ref<Source[]>([]); const title = ref(""); const authors = ref(""); const year = ref(""); const doi = ref(""); const error = ref(""); const busy = ref(false);
async function refresh() { sources.value = await listSources(props.projectId); }
async function submit() { busy.value = true; error.value = ""; try { await createSource(props.projectId, { title: title.value, authors: authors.value || undefined, year: year.value ? Number(year.value) : undefined, doi: doi.value || undefined }); title.value = ""; authors.value = ""; year.value = ""; doi.value = ""; await refresh(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Не удалось сохранить источник"; } finally { busy.value = false; } }
async function onUpload(source: Source, event: { files: File | File[] }) { const file = Array.isArray(event.files) ? event.files[0] : event.files; if (!file) return; try { await uploadSourceFile(props.projectId, source.id, file); await refresh(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Не удалось загрузить PDF"; } }
async function downloadFile(source: Source, file: Source["files"][number]) { try { await downloadSourceFile(props.projectId, source.id, file.id); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Не удалось скачать PDF"; } }
async function removeFile(source: Source, file: Source["files"][number]) { if (!window.confirm(`Удалить PDF «${file.original_name}»? Связанные фрагменты и evidence требуют сохранения этой версии.`)) return; try { await deleteSourceFile(props.projectId, source.id, file.id); await refresh(); } catch (reason) { error.value = reason instanceof Error ? reason.message : "Не удалось удалить PDF"; } }
onMounted(() => void refresh().catch(reason => { error.value = reason instanceof Error ? reason.message : "Не удалось загрузить библиотеку"; }));
</script>
<template>
  <section class="library-panel" aria-labelledby="library-title">
    <h2 id="library-title">Библиотека источников</h2>
    <Message v-if="error" severity="error" :closable="true" @close="error = ''">{{ error }}</Message>
    <form class="source-form" @submit.prevent="submit">
      <label>Название<InputText v-model="title" required maxlength="500" /></label>
      <label>Авторы<InputText v-model="authors" maxlength="4000" /></label>
      <label>Год<InputText v-model="year" inputmode="numeric" /></label>
      <label>DOI<InputText v-model="doi" maxlength="255" /></label>
      <Button type="submit" label="Добавить источник" :disabled="busy || !title.trim()" />
    </form>
    <Card v-for="source in sources" :key="source.id" class="source-card">
      <template #title>{{ source.title }}</template>
      <template #content>
        <p>{{ [source.authors, source.year, source.doi].filter(Boolean).join(" · ") || "Метаданные добавлены вручную" }}</p>
        <p v-if="source.files.length === 0">PDF ещё не загружен.</p>
        <ul v-else><li v-for="file in source.files" :key="file.id"><Button :label="`${file.original_name} · версия ${file.version}`" text @click="downloadFile(source, file)" /><Button label="Удалить" severity="danger" text @click="removeFile(source, file)" /></li></ul>
        <FileUpload name="file" accept="application/pdf,.pdf" :max-file-size="26214400" choose-label="Выбрать PDF" upload-label="Загрузить" :show-cancel-button="false" :custom-upload="true" @uploader="event => onUpload(source, event)" />
      </template>
    </Card>
  </section>
</template>
<style scoped>
.library-panel{display:grid;gap:1rem;margin-top:1.5rem;padding:1.25rem;border:1px solid var(--p-content-border-color);border-radius:var(--p-content-border-radius);background:var(--p-surface-0)}
.library-panel h2{margin:0}.source-form{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));align-items:end;gap:.8rem}.source-form label{display:grid;gap:.35rem;font-size:.85rem}.source-card p{margin:.25rem 0 .75rem}
</style>
