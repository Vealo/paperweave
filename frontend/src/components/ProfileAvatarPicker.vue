<script setup lang="ts">
import FileUpload from "primevue/fileupload";
import Message from "primevue/message";

withDefaults(defineProps<{
  disabled?: boolean;
  error?: string;
  notice?: string;
  title?: string;
}>(), { disabled: false, error: "", notice: "", title: "Фотография профиля" });

const emit = defineEmits<{
  select: [file: File];
  invalid: [message: string];
}>();

function onUploadSelection(event: { files: File | File[] }): void {
  const file = Array.isArray(event.files) ? event.files[0] : event.files;
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) {
    emit("invalid", "Размер аватара не должен превышать 5 МБ.");
    return;
  }
  if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
    emit("invalid", "Выберите файл PNG, JPEG или WebP.");
    return;
  }
  emit("select", file);
}
</script>

<template>
  <section class="profile-avatar-picker">
    <h2>{{ title }}</h2>
    <p>Загрузите PNG, JPEG или WebP размером до 5 МБ.</p>
    <FileUpload
      mode="basic"
      name="avatar"
      accept="image/png,image/jpeg,image/webp"
      :max-file-size="5242880"
      :auto="true"
      :custom-upload="true"
      choose-label="Загрузить аватар"
      :disabled="disabled"
      @uploader="onUploadSelection"
    />
    <Message v-if="error" severity="error" :closable="false">{{ error }}</Message>
    <Message v-if="notice" severity="success" :closable="false">{{ notice }}</Message>
  </section>
</template>
