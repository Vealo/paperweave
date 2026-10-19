import { computed, onBeforeUnmount, onMounted, ref } from "vue";

import { getReadiness } from "../api/projects";

export type HealthState = "checking" | "available" | "not_ready" | "no_connection";
type TagSeverity = "info" | "success" | "warn" | "danger";

export function useHealthStatus() {
  const state = ref<HealthState>("checking");
  let timer: number | undefined;
  let requestInFlight = false;

  async function checkHealth(): Promise<void> {
    if (requestInFlight) return;
    requestInFlight = true;
    try {
      state.value = (await getReadiness()) ? "available" : "not_ready";
    } catch {
      state.value = "no_connection";
    } finally {
      requestInFlight = false;
    }
  }

  const label = computed(() => {
    const labels: Record<HealthState, string> = {
      checking: "Проверяем API",
      available: "API доступен",
      not_ready: "База данных недоступна",
      no_connection: "Нет соединения с API",
    };
    return labels[state.value];
  });

  const severity = computed<TagSeverity>(() => {
    const severities: Record<HealthState, TagSeverity> = {
      checking: "info",
      available: "success",
      not_ready: "warn",
      no_connection: "danger",
    };
    return severities[state.value];
  });

  onMounted(() => {
    void checkHealth();
    timer = window.setInterval(() => void checkHealth(), 10_000);
  });

  onBeforeUnmount(() => {
    if (timer !== undefined) window.clearInterval(timer);
  });

  return { state, label, severity, refresh: checkHealth };
}
