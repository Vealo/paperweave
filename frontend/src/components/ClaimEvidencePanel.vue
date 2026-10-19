<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import Tag from "primevue/tag";
import Message from "primevue/message";
import { addEvidenceLink, createClaim, listClaims, reviewEvidenceLink, retractEvidenceLink, type Claim } from "../api/evidence";
import { listPassages, listSources, type SourcePassage } from "../api/library";

const props = defineProps<{ projectId: string; selectedText: string; blockPosition: number; disabled: boolean }>();
const emit = defineEmits<{ navigate: [position: number] }>();
const claims = ref<Claim[]>([]);
const passages = ref<SourcePassage[]>([]);
const claimText = ref("");
const passageId = ref<string | null>(null);
const relation = ref("supports");
const error = ref("");
const loading = ref(false);
const relations = ["supports", "contradicts", "contextualizes"];
const passageOptions = computed(() => passages.value.map((p) => ({ label: `Страница ${p.page_number}: ${p.text.slice(0, 100)}`, value: p.id })));

async function load(): Promise<void> {
  loading.value = true; error.value = "";
  try {
    claims.value = await listClaims(props.projectId);
    const sources = await listSources(props.projectId);
    const all = await Promise.all(sources.flatMap((source) => source.files.map((file) => listPassages(props.projectId, source.id, file.id))));
    passages.value = all.flat();
  } catch (reason) { error.value = reason instanceof Error ? reason.message : "Не удалось загрузить доказательства."; }
  finally { loading.value = false; }
}
async function addClaim(): Promise<void> {
  const value = (claimText.value || props.selectedText).trim();
  if (!value) return;
  try { await createClaim(props.projectId, value, props.blockPosition); claimText.value = ""; await load(); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Не удалось создать утверждение."; }
}
async function link(claim: Claim): Promise<void> {
  if (!passageId.value) return;
  try { await addEvidenceLink(props.projectId, claim.id, passageId.value, relation.value as "supports" | "contradicts" | "contextualizes"); await load(); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Не удалось связать фрагмент."; }
}
async function review(linkId: string, decision: "verified" | "rejected"): Promise<void> {
  try { await reviewEvidenceLink(props.projectId, linkId, decision); await load(); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Не удалось сохранить проверку."; }
}
async function unlink(linkId: string): Promise<void> {
  try { await retractEvidenceLink(props.projectId, linkId); await load(); }
  catch (reason) { error.value = reason instanceof Error ? reason.message : "Не удалось отвязать фрагмент."; }
}
watch(() => props.projectId, () => void load());
onMounted(() => void load());
</script>

<template>
  <section class="evidence-panel" aria-labelledby="evidence-title">
    <div class="evidence-panel__heading"><div><p class="eyebrow">Аргументация</p><h2 id="evidence-title">Утверждения и основания</h2></div><Button label="Обновить" severity="secondary" text :loading="loading" @click="void load()" /></div>
    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
    <Message v-if="disabled" severity="info" :closable="false">Сохраните рукопись, чтобы связать утверждение с её текущей версией.</Message>
    <div class="evidence-panel__create"><InputText v-model="claimText" :disabled="disabled" :placeholder="selectedText || 'Текст утверждения из рукописи'" aria-label="Утверждение" /><Button label="Добавить утверждение" icon="pi pi-plus" :disabled="disabled || !(claimText.trim() || selectedText.trim())" @click="void addClaim()" /></div>
    <div class="evidence-panel__link"><Select v-model="passageId" :disabled="disabled" :options="passageOptions" option-label="label" option-value="value" placeholder="Извлечённый фрагмент PDF" aria-label="Фрагмент источника" /><Select v-model="relation" :disabled="disabled" :options="relations" placeholder="Тип связи" aria-label="Тип связи" /><span class="evidence-panel__hint">Цитата и извлечение сами по себе не являются проверкой.</span></div>
    <article v-for="claim in claims" :key="claim.id" class="claim-card">
      <p class="eyebrow">Claim v{{ claim.version }} · рукопись v{{ claim.manuscript_version }} · блок {{ claim.block_position }}</p><p class="claim-card__text">{{ claim.text }}</p>
      <div v-if="claim.links.length" class="claim-card__links"><div v-for="item in claim.links" :key="item.id" class="evidence-link">
        <div><Tag :value="item.relation" severity="info" /><Tag :value="item.review_state" :severity="item.review_state === 'verified' ? 'success' : item.review_state === 'needs_review' ? 'warn' : 'secondary'" /><p>{{ item.source_title }} · стр. {{ item.passage_page }}</p><blockquote>{{ item.passage_text }}</blockquote><small>{{ item.reviewer_id ? `Проверил ${item.reviewer_id} · ${item.decided_at}` : 'Ещё не проверено владельцем' }}</small></div>
        <div v-if="item.review_state === 'unreviewed' || item.review_state === 'needs_review'" class="evidence-link__actions"><Button label="Проверено" size="small" :disabled="disabled" @click="void review(item.id, 'verified')" /><Button label="Отклонить" size="small" severity="danger" outlined :disabled="disabled" @click="void review(item.id, 'rejected')" /></div><Button v-if="item.review_state !== 'retracted'" label="Отвязать" severity="secondary" text size="small" :disabled="disabled" @click="void unlink(item.id)" />
      </div></div>
      <div v-else class="evidence-panel__hint">Пока только текст утверждения; источник и проверенное evidence не добавлены.</div>
      <Button label="Связать с фрагментом" severity="secondary" outlined size="small" :disabled="disabled || !passageId" @click="void link(claim)" />
      <Button label="К утверждению в рукописи" severity="secondary" text size="small" @click="emit('navigate', claim.block_position)" />
    </article>
    <p v-if="!claims.length && !loading" class="evidence-panel__hint">Выделите фрагмент рукописи и добавьте утверждение. Затем свяжите его с извлечённой страницей и отдельно отметьте review.</p>
  </section>
</template>

<style scoped>
.evidence-panel{display:grid;gap:1rem;margin-top:1.5rem;padding:1.25rem;border:1px solid var(--p-content-border-color);border-radius:var(--p-content-border-radius);background:var(--p-surface-0)}.evidence-panel__heading,.evidence-panel__create,.evidence-panel__link,.evidence-link,.evidence-link__actions{display:flex;align-items:center;gap:.75rem;flex-wrap:wrap}.evidence-panel h2{margin:.1rem 0}.evidence-panel__create>*:first-child{flex:1;min-width:16rem}.evidence-panel__link>*{flex:1;min-width:12rem}.claim-card{display:grid;gap:.6rem;padding:1rem;border:1px solid var(--p-content-border-color);border-radius:var(--p-content-border-radius)}.claim-card__text{margin:0;font-weight:600}.claim-card__links{display:grid;gap:.5rem}.evidence-link{justify-content:space-between;padding:.75rem;background:var(--p-surface-50);border-radius:var(--p-content-border-radius)}.evidence-link p,.evidence-link small{display:block;margin:.35rem 0}.evidence-panel__hint{color:var(--p-text-muted-color);font-size:.9rem}
</style>
