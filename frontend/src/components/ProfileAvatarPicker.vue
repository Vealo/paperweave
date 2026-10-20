<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'

const props = withDefaults(defineProps<{
  title?: string
  currentAvatarUrl?: string | null
  disabled?: boolean
  error?: string
  notice?: string
  uploading?: boolean
}>(), { title: 'Аватар пользователя', currentAvatarUrl: null, disabled: false, error: '', notice: '', uploading: false })

const emit = defineEmits<{
  select: [file: File]
  invalid: [message: string]
}>()

const input = ref<HTMLInputElement>()
const dialogVisible = ref(false)
const image = ref<HTMLImageElement>()
const objectUrl = ref('')
const selectedName = ref('')
const processing = ref(false)
const imageError = ref('')
const confirmed = ref(false)
const zoom = ref(1)
const natural = ref({ width: 0, height: 0 })
const viewport = ref(0)
const pan = ref({ x: 0, y: 0 })
const drag = ref<{ pointerId: number; x: number; y: number; panX: number; panY: number }>()
const cropFrame = ref<HTMLElement>()
let resizeObserver: ResizeObserver | undefined

const baseScale = computed(() => {
  if (!natural.value.width || !natural.value.height || !viewport.value) return 1
  return Math.max(viewport.value / natural.value.width, viewport.value / natural.value.height)
})
const imageStyle = computed(() => {
  const width = natural.value.width * baseScale.value * zoom.value
  const height = natural.value.height * baseScale.value * zoom.value
  const x = (viewport.value - width) / 2 + pan.value.x
  const y = (viewport.value - height) / 2 + pan.value.y
  return { width: `${width}px`, height: `${height}px`, transform: `translate(${x}px, ${y}px)` }
})

function cleanupUrl() {
  if (objectUrl.value) URL.revokeObjectURL(objectUrl.value)
  objectUrl.value = ''
}

function clearSelection() {
  cleanupUrl()
  selectedName.value = ''
  imageError.value = ''
  natural.value = { width: 0, height: 0 }
  pan.value = { x: 0, y: 0 }
  zoom.value = 1
}

function onChoose(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  target.value = ''
  if (!file) return
  if (!['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
    emit('invalid', 'Выберите изображение PNG, JPEG или WebP.')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    emit('invalid', 'Размер изображения не должен превышать 5 МБ.')
    return
  }
  emit('invalid', '')
  clearSelection()
  confirmed.value = false
  selectedName.value = file.name
  objectUrl.value = URL.createObjectURL(file)
  dialogVisible.value = true
}

function onImageLoad() {
  if (!image.value) return
  natural.value = { width: image.value.naturalWidth, height: image.value.naturalHeight }
  if (!natural.value.width || !natural.value.height) onImageError()
}

function onImageError() {
  imageError.value = 'Не удалось прочитать изображение. Выберите другой файл.'
  emit('invalid', imageError.value)
}

function clampPan(x: number, y: number) {
  const width = natural.value.width * baseScale.value * zoom.value
  const height = natural.value.height * baseScale.value * zoom.value
  const maxX = Math.max(0, (width - viewport.value) / 2)
  const maxY = Math.max(0, (height - viewport.value) / 2)
  pan.value = { x: Math.max(-maxX, Math.min(maxX, x)), y: Math.max(-maxY, Math.min(maxY, y)) }
}

function onZoom(event: Event) {
  const nextZoom = Number((event.target as HTMLInputElement).value)
  zoom.value = nextZoom
  clampPan(pan.value.x, pan.value.y)
}

function startDrag(event: PointerEvent) {
  if (event.button !== 0) return
  drag.value = { pointerId: event.pointerId, x: event.clientX, y: event.clientY, panX: pan.value.x, panY: pan.value.y }
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}

function moveDrag(event: PointerEvent) {
  if (!drag.value || drag.value.pointerId !== event.pointerId) return
  clampPan(drag.value.panX + event.clientX - drag.value.x, drag.value.panY + event.clientY - drag.value.y)
}

function endDrag(event: PointerEvent) {
  if (drag.value?.pointerId === event.pointerId) drag.value = undefined
}

function onCropKeydown(event: KeyboardEvent) {
  const distance = event.shiftKey ? 25 : 10
  const moves: Record<string, [number, number]> = {
    ArrowLeft: [distance, 0], ArrowRight: [-distance, 0], ArrowUp: [0, distance], ArrowDown: [0, -distance]
  }
  const offset = moves[event.key]
  if (!offset) return
  event.preventDefault()
  clampPan(pan.value.x + offset[0], pan.value.y + offset[1])
}

async function confirmCrop() {
  if (!image.value || !natural.value.width || processing.value) return
  processing.value = true
  try {
    const scale = baseScale.value * zoom.value
    const sourceSize = viewport.value / scale
    const sourceX = (natural.value.width - sourceSize) / 2 - pan.value.x / scale
    const sourceY = (natural.value.height - sourceSize) / 2 - pan.value.y / scale
    const canvas = document.createElement('canvas')
    canvas.width = 512
    canvas.height = 512
    const context = canvas.getContext('2d')
    if (!context) throw new Error('Не удалось подготовить изображение.')
    context.drawImage(image.value, sourceX, sourceY, sourceSize, sourceSize, 0, 0, 512, 512)
    const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob(value => value ? resolve(value) : reject(new Error('Не удалось подготовить изображение.')), 'image/png'))
    const stem = selectedName.value.replace(/\.[^.]+$/, '').replace(/[^\p{L}\p{N}_-]+/gu, '-').slice(0, 80) || 'avatar'
    confirmed.value = true
    emit('select', new File([blob], `${stem}.png`, { type: 'image/png', lastModified: Date.now() }))
    dialogVisible.value = false
  } catch (error) {
    emit('invalid', error instanceof Error ? error.message : 'Не удалось подготовить изображение.')
  } finally {
    processing.value = false
  }
}

function onHide() {
  const submittedName = confirmed.value ? selectedName.value : ''
  clearSelection()
  selectedName.value = submittedName
  confirmed.value = false
  resizeObserver?.disconnect()
  resizeObserver = undefined
}

watch(dialogVisible, async visible => {
  if (!visible) return
  await nextTick()
  if (cropFrame.value) {
    resizeObserver = new ResizeObserver(entries => {
      viewport.value = entries[0]?.contentRect.width ?? 0
      clampPan(pan.value.x, pan.value.y)
    })
    resizeObserver.observe(cropFrame.value)
    viewport.value = cropFrame.value.getBoundingClientRect().width
  }
})

onBeforeUnmount(() => { cleanupUrl(); resizeObserver?.disconnect() })
</script>

<template>
  <div class="profile-avatar-picker">
    <div v-if="currentAvatarUrl" class="profile-avatar-picker__current">
      <img :src="currentAvatarUrl" alt="Текущий аватар" />
      <span>Текущий аватар</span>
    </div>
    <strong>{{ title }}</strong>
    <p class="profile-avatar-picker__hint">Загрузите PNG, JPEG или WebP размером до 5 МБ.</p>
    <input ref="input" class="profile-avatar-picker__input" type="file" accept="image/png,image/jpeg,image/webp" :disabled="disabled" @change="onChoose" />
    <Button label="Загрузить аватар" icon="pi pi-plus" :disabled="disabled" @click="input?.click()" />
    <span v-if="selectedName" class="profile-avatar-picker__filename" aria-live="polite">{{ uploading || disabled ? 'Загрузка:' : 'Выбрано:' }} {{ selectedName }}</span>
    <p v-if="error" class="profile-avatar-picker__error" role="alert">{{ error }}</p>
    <p v-if="notice" class="profile-avatar-picker__notice" role="status">{{ notice }}</p>

    <Dialog v-model:visible="dialogVisible" modal header="Предпросмотр аватара" class="pw-modal-fullscreen avatar-crop-dialog" :closable="!processing" :close-on-escape="!processing" @hide="onHide">
      <div class="avatar-crop-dialog__content">
        <p>{{ processing ? 'Подготовка изображения…' : `Выбрано: ${selectedName}` }}</p>
        <p v-if="imageError" class="profile-avatar-picker__error" role="alert">{{ imageError }}</p>
        <p>Перемещайте изображение мышью или стрелками. Масштаб регулируется ползунком.</p>
        <div ref="cropFrame" class="avatar-crop-dialog__crop" role="group" tabindex="0" aria-label="Область кадрирования аватара" @keydown="onCropKeydown" @pointerdown="startDrag" @pointermove="moveDrag" @pointerup="endDrag" @pointercancel="endDrag">
          <img v-if="objectUrl" ref="image" :src="objectUrl" alt="Предпросмотр кадрирования" :style="imageStyle" draggable="false" @load="onImageLoad" @error="onImageError" />
        </div>
        <label class="avatar-crop-dialog__zoom">Масштаб
          <input type="range" min="1" max="3" step="0.01" :value="zoom" aria-label="Масштаб изображения" @input="onZoom" />
        </label>
      </div>
      <template #footer>
        <Button label="Отмена" severity="secondary" outlined :disabled="processing" @click="dialogVisible = false" />
        <Button label="Использовать изображение" :loading="processing" :disabled="!natural.width" @click="confirmCrop" />
      </template>
    </Dialog>
  </div>
</template>

<style scoped>
.profile-avatar-picker { display: flex; flex-wrap: wrap; align-items: center; gap: .65rem; }
.profile-avatar-picker__hint, .profile-avatar-picker__error, .profile-avatar-picker__notice { flex-basis: 100%; margin: 0; }
.profile-avatar-picker__hint, .profile-avatar-picker__filename { color: var(--p-text-muted-color); font-size: .875rem; }
.profile-avatar-picker__filename { overflow-wrap: anywhere; }
.profile-avatar-picker__error { color: var(--p-red-600); }
.profile-avatar-picker__input { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
.profile-avatar-picker__input:focus-visible + button { outline: 2px solid var(--p-primary-color); outline-offset: 2px; }
.profile-avatar-picker__current { display: flex; align-items: center; gap: .6rem; flex-basis: 100%; }
.profile-avatar-picker__current img { width: 3rem; height: 3rem; border-radius: 50%; object-fit: cover; }
.avatar-crop-dialog__content { display: grid; justify-items: center; gap: 1.25rem; }
.avatar-crop-dialog__content > p { margin: 0; text-align: center; }
.avatar-crop-dialog__crop { position: relative; width: min(78vw, 52dvh, 480px); aspect-ratio: 1; overflow: hidden; border-radius: .75rem; background: #111827; touch-action: none; cursor: grab; outline-offset: 4px; }
.avatar-crop-dialog__crop:active { cursor: grabbing; }
.avatar-crop-dialog__crop::after { position: absolute; inset: 0; border: 1px solid rgb(255 255 255 / 70%); border-radius: inherit; content: ''; pointer-events: none; }
.avatar-crop-dialog__crop img { position: absolute; top: 0; left: 0; max-width: none; user-select: none; pointer-events: none; }
.avatar-crop-dialog__zoom { display: grid; width: min(100%, 32rem); gap: .5rem; }
.avatar-crop-dialog__zoom input { width: 100%; }
@media (max-width: 600px) { .avatar-crop-dialog__crop { width: min(88vw, 52dvh); } }
</style>
