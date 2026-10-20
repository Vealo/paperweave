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
  checked: false
  evidence: []
- id: AC-2
  text: Перед отправкой открывается полноэкранный предпросмотр с квадратной областью
    кадрирования и масштабированием.
  checked: false
  evidence: []
- id: AC-3
  text: Загрузка начинается только после явного подтверждения; отмена не меняет текущий
    аватар.
  checked: false
  evidence: []
- id: AC-4
  text: При неудачной замене сохраняется прежний аватар, а интерфейс показывает ошибку
    и позволяет повторить загрузку.
  checked: false
  evidence: []
- id: AC-5
  text: Диалог доступен с клавиатуры, корректно управляет фокусом и поддерживает мобильный
    viewport.
  checked: false
  evidence: []
status: todo
revision: 2
blockers: []
created_at: '2026-10-20T08:25:54Z'
updated_at: '2026-10-20T08:45:33Z'
---

## Outcome

Пользователь осознанно выбирает область изображения и подтверждает загрузку аватара.

## Scope

Общий интерфейс выбора аватара для собственного профиля и формы создания пользователя; повторное использование PrimeVue и текущего API.

## Notes

This task owns browser-side avatar preview and crop selection; server-side image decoding and normalization belong to TASK-018.
