---
schema: task-store/v1
id: TASK-003
key: IMP-imp-2026-001-mvp-foundation:P3:vue-project-workflow
title: Реализовать интерфейс проектов на Vue и PrimeVue
source_ref: request:2026-10-19-paperweave-mvp-foundation
parent_ref: imp-2026-001-mvp-foundation
phase: P3
priority: high
depends_on:
- TASK-002
criteria:
- id: AC-1
  text: Главная при открытии получает readiness и список; health polling раз в 10
    секунд не перекрывается и прекращается при закрытии страницы.
  checked: false
  evidence: []
- id: AC-2
  text: Форма создаёт проект через POST, блокирует повторный клик во время запроса,
    затем обновляет список; при ошибке введённые данные сохраняются и POST автоматически
    не повторяется.
  checked: false
  evidence: []
- id: AC-3
  text: Список позволяет обновить данные и перейти к карточке с name, description,
    id, created_at и возвратом.
  checked: false
  evidence: []
- id: AC-4
  text: Состояния checking/available/not ready/no connection видимы; недоступный API
    не ломает приложение.
  checked: false
  evidence: []
- id: AC-5
  text: Стандартное оформление использует готовые PrimeVue-компоненты согласно дизайн-коду;
    проверки typecheck/build проходят.
  checked: false
  evidence: []
status: todo
revision: 1
blockers: []
created_at: '2026-10-19T11:59:23Z'
updated_at: '2026-10-19T11:59:23Z'
---

## Outcome

Пользователь через браузер видит доступность API, создаёт проект, обновляет список и открывает страницу проекта.

## Scope

Реализовать Vue 3 + TypeScript + PrimeVue 4 UI по docs/design-system.md: главную, health status, список/создание и детальную страницу. Не добавлять Tiptap editor, PDF, LLM или иные будущие продуктовые сценарии.

## Notes

