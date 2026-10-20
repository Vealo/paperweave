<script setup lang="ts">
import Button from "primevue/button";
import { RouterLink, type RouteLocationRaw } from "vue-router";

export type AppHeaderAction =
  | { label: string; to: RouteLocationRaw }
  | { label: string; onClick: () => void; disabled?: boolean };

defineProps<{ actions: AppHeaderAction[] }>();
</script>

<template>
  <nav v-if="actions.length" class="app-header__actions" aria-label="Действия текущей страницы">
    <template v-for="(action, index) in actions.slice(0, 3)" :key="`${action.label}-${index}`">
      <RouterLink v-if="'to' in action" :to="action.to" custom v-slot="{ navigate }">
        <Button :label="action.label" severity="secondary" text @click="navigate" />
      </RouterLink>
      <Button
        v-else
        :label="action.label"
        severity="secondary"
        text
        :disabled="action.disabled"
        @click="action.onClick"
      />
    </template>
  </nav>
</template>
