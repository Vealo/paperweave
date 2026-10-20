---
schema: task-store/v1
id: TASK-017
key: avatar-crop-flow
title: Реализовать предпросмотр и кадрирование аватара
source_ref: user:2026-10-20-profile-audit
parent_ref: TASK-015
phase: null
priority: high
depends_on:
- TASK-015
criteria:
- id: AC-1
  text: После выбора файла отображаются его имя, проверка формата/размера и состояние
    обработки; ошибки выбора объясняются рядом с контролом.
  checked: true
  evidence:
  - frontend/src/components/ProfileAvatarPicker.vue filename, MIME/size validation,
    decode errors, processing/upload status
- id: AC-2
  text: Перед отправкой открывается полноэкранный предпросмотр с квадратной областью
    кадрирования и масштабированием.
  checked: true
  evidence:
  - frontend/src/components/ProfileAvatarPicker.vue PrimeVue full-screen Dialog, square
    crop surface, zoom range and clamped pointer pan
- id: AC-3
  text: Загрузка начинается только после явного подтверждения; отмена не меняет текущий
    аватар.
  checked: true
  evidence:
  - frontend/src/components/ProfileAvatarPicker.vue emits only after Использовать
    изображение; cancel/escape only closes and discards
- id: AC-4
  text: При неудачной замене сохраняется прежний аватар, а интерфейс показывает ошибку
    и позволяет повторить загрузку.
  checked: true
  evidence:
  - frontend/src/views/ProfileView.vue retains currentUser avatar on failed upload
    and exposes retry; picker retains filename and error
- id: AC-5
  text: Диалог доступен с клавиатуры, корректно управляет фокусом и поддерживает мобильный
    viewport.
  checked: true
  evidence:
  - frontend/src/components/ProfileAvatarPicker.vue keyboard arrow pan and accessible
    controls; PrimeVue modal focus handling; responsive crop sizing
status: in_progress
revision: 5
blockers: []
created_at: '2026-10-20T08:25:54Z'
updated_at: '2026-10-20T09:17:17Z'
next_action: Finalize TASK-017 after independent re-review and scoped diff check
progress_note: Crop flow and profile upload state pass typecheck/build; review fixes
  applied
---

## Outcome

Пользователь осознанно выбирает область изображения и подтверждает загрузку аватара.

## Scope

Общий интерфейс выбора аватара для собственного профиля и формы создания пользователя; повторное использование PrimeVue и текущего API.

## Notes

This task owns browser-side avatar preview and crop selection; server-side image decoding and normalization belong to TASK-018.

## TASK-017 implementation and review (2026-10-20)

- Replaced immediate FileUpload emission with a shared PrimeVue full-screen crop dialog. It validates PNG/JPEG/WebP and 5 MB, reports decode failures, provides square crop with zoom and bounded pointer/keyboard panning, then emits a normalized 512x512 PNG only after confirmation.
- Cancel and Escape discard the pending image without emitting. Confirmed filename remains visible while a profile upload is pending; ProfileView prevents parallel avatar uploads. Existing API parents retain their old avatar on failed request and surface the error for retry.
- Independent read-only review found three AC-1/integration gaps (pending filename/status, decode failure, concurrent profile uploads); all were addressed before final review. App/Profile/Users handlers remain compatible with the emitted File payload.
- `npm run typecheck` and `npm run build` passed after the corrections. Build keeps existing warnings for `/runtime-config.js` and the >500 kB JS chunk. No runtime browser/keyboard interaction test was run; accessibility evidence is source review plus PrimeVue Dialog behavior and responsive styles.

## TASK-017 implementation and review (2026-10-20)

- Replaced immediate FileUpload emission with a shared PrimeVue full-screen crop dialog. It validates PNG/JPEG/WebP and 5 MB, reports decode failures, provides square crop with zoom and bounded pointer/keyboard panning, then emits a normalized 512x512 PNG only after confirmation.
- Cancel and Escape discard the pending image without emitting. Confirmed filename remains visible while a profile upload is pending; ProfileView prevents parallel avatar uploads. Existing API parents retain their old avatar on failed request and surface the error for retry.
- Independent read-only review found three AC-1/integration gaps (pending filename/status, decode failure, concurrent profile uploads); all were addressed before final review. App/Profile/Users handlers remain compatible with the emitted File payload.
- `npm run typecheck` and `npm run build` passed after the corrections. Build keeps existing warnings for `/runtime-config.js` and the >500 kB JS chunk. No runtime browser/keyboard interaction test was run; accessibility evidence is source review plus PrimeVue Dialog behavior and responsive styles.
