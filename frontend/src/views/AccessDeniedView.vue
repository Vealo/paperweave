<script setup lang="ts">
import { RouterLink } from "vue-router";
import Button from "primevue/button";
import Card from "primevue/card";
import Message from "primevue/message";
</script>

<template>
  <section class="auth-page">
    <Card class="auth-card">
      <template #title>Недостаточно прав</template>
      <template #content>
        <Message severity="error" :closable="false">
          Эта операция доступна только владельцу локального пространства.
        </Message>
        <RouterLink to="/" custom v-slot="{ navigate }">
          <Button label="Вернуться к проектам" severity="secondary" @click="navigate" />
        </RouterLink>
      </template>
    </Card>
  </section>
</template>
