<script setup lang="ts">
import { computed } from "vue";
import Avatar from "primevue/avatar";

const props = withDefaults(defineProps<{
  displayName: string;
  email?: string | null;
  avatarUrl?: string | null;
  variant?: "header" | "panel" | "preview";
}>(), { variant: "panel" });

const initials = computed(() => props.displayName.trim().split(/\s+/).slice(0, 2).map((part) => part[0]?.toLocaleUpperCase()).join("") || "?");
</script>

<template>
  <div class="profile-identity" :class="`profile-identity--${variant}`">
    <Avatar
      :image="avatarUrl || undefined"
      :label="initials"
      shape="circle"
      class="profile-identity__avatar"
      :aria-label="`Аватар ${displayName}`"
      :pt="{ image: { crossorigin: 'use-credentials' } }"
    />
    <span class="profile-identity__details">
      <strong>{{ displayName }}</strong>
      <small v-if="email">{{ email }}</small>
    </span>
  </div>
</template>
