<script setup lang="ts">
import { computed, ref, watch } from "vue";
import Button from "primevue/button";
import Card from "primevue/card";
import Message from "primevue/message";
import Tag from "primevue/tag";
import Textarea from "primevue/textarea";
import { createAIProposal, decideAIProposal, type AIProposal } from "../api/aiProposals";
import { getManuscriptVersion, type Manuscript, type ManuscriptRevision } from "../api/manuscript";

const props = defineProps<{
  projectId: string;
  selectedText: string;
  targetPosition: number;
  manuscriptVersion: number | null;
  disabled: boolean;
}>();
const emit = defineEmits<{ applied: [manuscript: Manuscript] }>();
const instruction = ref("Уточнить формулировку");
const normalizedInstruction = computed(() => instruction.value.trim());
const requestKey = ref<string | null>(null);
const requestManifest = ref("");
const proposal = ref<AIProposal | null>(null);
const originalRevision = ref<ManuscriptRevision | null>(null);
const showOriginal = ref(false);
const busy = ref(false);
const error = ref("");
const info = ref("");

watch(() => props.projectId, () => {
  proposal.value = null;
  originalRevision.value = null;
  showOriginal.value = false;
  requestKey.value = null;
  requestManifest.value = "";
  error.value = "";
  info.value = "";
});

function collectText(node: unknown): string {
  if (!node || typeof node !== "object") return "";
  const value = node as { type?: string; text?: string; content?: unknown[] };
  if (value.type === "text") return value.text ?? "";
  const separator = value.type === "doc" ? "\n\n" : "";
  return (value.content ?? []).map(collectText).join(separator);
}

async function requestProposal(): Promise<void> {
  if (props.disabled || !props.manuscriptVersion || !props.selectedText.trim()) return;
  const manifestIdentity = JSON.stringify({
    expected_version: props.manuscriptVersion,
    target_position: props.targetPosition,
    selected_text: props.selectedText,
    instruction: normalizedInstruction.value,
  });
  if (!requestKey.value || requestManifest.value !== manifestIdentity) {
    requestKey.value = crypto.randomUUID();
    requestManifest.value = manifestIdentity;
  }
  busy.value = true;
  error.value = "";
  info.value = "";
  try {
    proposal.value = await createAIProposal(props.projectId, {
      expected_version: props.manuscriptVersion,
      target_position: props.targetPosition,
      selected_text: props.selectedText,
      instruction: normalizedInstruction.value,
      idempotency_key: requestKey.value,
    });
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Не удалось подготовить предложение.";
  } finally {
    busy.value = false;
  }
}

function resetProposal(): void {
  proposal.value = null;
  originalRevision.value = null;
  showOriginal.value = false;
  requestKey.value = null;
  requestManifest.value = "";
  info.value = "";
  error.value = "";
}

async function decide(decision: "accepted" | "rejected"): Promise<void> {
  if (!proposal.value) return;
  busy.value = true;
  error.value = "";
  info.value = "";
  try {
    const result = await decideAIProposal(props.projectId, proposal.value.id, decision);
    proposal.value = result;
    if (decision === "accepted" && result.manuscript) {
      emit("applied", result.manuscript);
      originalRevision.value = await getManuscriptVersion(props.projectId, result.target_version);
    } else info.value = "Предложение отклонено; рукопись не изменена.";
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "Не удалось сохранить решение.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <Card class="ai-proposal-panel" aria-label="AI-предложение">
    <template #title>AI-предложение</template>
    <template #content>
      <Message severity="warn" :closable="false">Демонстрационный mock. Текст не отправляется внешнему провайдеру.</Message>
      <label class="ai-field-label" for="ai-instruction">Инструкция</label>
      <Textarea id="ai-instruction" v-model="instruction" rows="2" auto-resize maxlength="1000" :disabled="busy || !!proposal" />
      <div class="ai-manifest" aria-label="Контекст, который будет использован">
        <strong>Передаваемый контекст</strong>
        <dl>
          <dt>Версия рукописи</dt><dd>{{ proposal?.context_manifest.target_version ?? manuscriptVersion ?? "Нет сохранённой версии" }}</dd>
          <dt>Позиция</dt><dd>{{ proposal?.context_manifest.target_position ?? targetPosition }}</dd>
          <dt>Выделенный текст</dt><dd class="ai-selected-text">{{ proposal ? proposal.context_manifest.selected_text : (selectedText || "Выделите текст в рукописи") }}</dd>
          <dt>Инструкция</dt><dd>{{ proposal ? proposal.context_manifest.instruction : normalizedInstruction }}</dd>
          <dt>Обработка</dt><dd>mock · локально</dd>
        </dl>
      </div>
      <Button v-if="!proposal" label="Подготовить mock-предложение" severity="secondary" outlined :loading="busy" :disabled="disabled || !selectedText.trim() || selectedText.length > 4000 || !normalizedInstruction" @click="void requestProposal()" />
      <template v-else>
        <Tag :value="proposal.status" severity="info" />
        <section v-if="proposal.suggestion" class="ai-suggestion">
          <strong>Предложение</strong>
          <p>{{ proposal.suggestion }}</p>
        </section>
        <div v-if="proposal.status === 'pending'" class="ai-actions">
          <Button label="Применить как новую версию" severity="primary" :loading="busy" :disabled="disabled" @click="void decide('accepted')" />
          <Button label="Отклонить" severity="secondary" text :loading="busy" @click="void decide('rejected')" />
        </div>
        <template v-else>
          <Button v-if="proposal.status === 'accepted'" label="Показать исходную версию" severity="secondary" text @click="showOriginal = !showOriginal" />
          <p v-if="showOriginal && originalRevision" class="ai-original-version"><strong>Исходная рукопись · версия {{ originalRevision.version }}</strong><br />{{ collectText(originalRevision.content) }}</p>
          <Button label="Новое предложение" severity="secondary" text @click="resetProposal" />
        </template>
      </template>
      <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
      <Message v-if="info" severity="success" :closable="false">{{ info }}</Message>
    </template>
  </Card>
</template>

<style scoped>
.ai-proposal-panel { margin-top: 1rem; }
.ai-field-label { display: block; margin: .75rem 0 .35rem; font-weight: 600; }
.ai-proposal-panel :deep(textarea) { width: 100%; }
.ai-manifest { margin: .8rem 0; padding: .75rem; border: 1px solid var(--p-content-border-color); border-radius: var(--p-border-radius-md); }
.ai-manifest dl { display: grid; grid-template-columns: 7rem minmax(0,1fr); gap: .4rem; font-size: .875rem; }
.ai-manifest dt { color: var(--p-text-muted-color); }
.ai-manifest dd { margin: 0; overflow-wrap: anywhere; }
.ai-selected-text { white-space: pre-wrap; }
.ai-suggestion { margin: .8rem 0; padding: .75rem; background: var(--p-surface-50); border-radius: var(--p-border-radius-md); white-space: pre-wrap; }
.ai-actions { display: flex; flex-wrap: wrap; gap: .5rem; }
.ai-original-version { margin-top: .75rem; padding: .75rem; border-inline-start: 3px solid var(--p-primary-color); white-space: pre-wrap; }
</style>
