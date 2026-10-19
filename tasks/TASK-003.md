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
  checked: true
  evidence:
  - source:frontend/src/composables/useHealthStatus.ts; browser:initial health UI;
    typecheck/build passed
  - post-merge:main 41eb96f; backend 17 passed; frontend typecheck/build passed
- id: AC-2
  text: Форма создаёт проект через POST, блокирует повторный клик во время запроса,
    затем обновляет список; при ошибке введённые данные сохраняются и POST автоматически
    не повторяется.
  checked: true
  evidence:
  - browser:created project; stopped-API submission showed error and retained both
    fields; source has no retry
- id: AC-3
  text: Список позволяет обновить данные и перейти к карточке с name, description,
    id, created_at и возвратом.
  checked: true
  evidence:
  - browser:project detail displayed name, description, UUID, created date; back/list
    links present
- id: AC-4
  text: Состояния checking/available/not ready/no connection видимы; недоступный API
    не ломает приложение.
  checked: true
  evidence:
  - 'browser:API available -> no connection while stopped -> available after restart;
    local DB outage: live 200, ready 503'
- id: AC-5
  text: Стандартное оформление использует готовые PrimeVue-компоненты согласно дизайн-коду;
    проверки typecheck/build проходят.
  checked: true
  evidence:
  - frontend npm run typecheck and npm run build passed; PrimeVue Aura controls used
    per docs/design-system.md
  - task commit 5f5c7f2 reachable from main 41eb96f
status: done
revision: 4
blockers: []
created_at: '2026-10-19T11:59:23Z'
updated_at: '2026-10-19T12:51:48Z'
progress_note: P3 integrated into main; post-merge backend/frontend checks green.
---

## Outcome

Пользователь через браузер видит доступность API, создаёт проект, обновляет список и открывает страницу проекта.

## Scope

Реализовать Vue 3 + TypeScript + PrimeVue 4 UI по docs/design-system.md: главную, health status, список/создание и детальную страницу. Не добавлять Tiptap editor, PDF, LLM или иные будущие продуктовые сценарии.

## Notes

