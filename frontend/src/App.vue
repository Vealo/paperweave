<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
import Tag from "primevue/tag";

import { useHealthStatus } from "./composables/useHealthStatus";

const health = useHealthStatus();
</script>

<template>
  <div class="app-shell">
    <header class="app-header">
      <div class="app-header__inner">
        <RouterLink class="brand" to="/" aria-label="PaperWeave — главная">
          <span class="brand__mark" aria-hidden="true">P</span>
          <span class="brand__name">PaperWeave</span>
        </RouterLink>

        <Tag :value="health.label.value" :severity="health.severity.value" />
      </div>
    </header>

    <main class="app-main">
      <RouterView />
    </main>

    <footer class="app-footer">PaperWeave · рабочее пространство исследования</footer>
  </div>
</template>
