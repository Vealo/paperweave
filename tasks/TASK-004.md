---
schema: task-store/v1
id: TASK-004
key: IMP-imp-2026-001-mvp-foundation:P4:compose-acceptance
title: Проверить сквозной запуск и сохранность данных MVP
source_ref: request:2026-10-19-paperweave-mvp-foundation
parent_ref: imp-2026-001-mvp-foundation
phase: P4
priority: high
depends_on:
- TASK-001
- TASK-002
- TASK-003
criteria:
- id: AC-1
  text: Чистый изолированный запуск ожидает готовность БД, завершает миграции до готовности
    приложения и открывает UI/API на настраиваемых loopback-портах.
  checked: false
  evidence: []
- id: AC-2
  text: Smoke сценарий создаёт проект через UI/API, останавливает приложение без удаления
    volume, запускает снова и подтверждает наличие проекта.
  checked: false
  evidence: []
- id: AC-3
  text: При ошибке миграции или недоступности БД приложение не объявляет readiness;
    live остаётся независимым от DB.
  checked: false
  evidence: []
- id: AC-4
  text: При API outage UI показывает отсутствие соединения и восстанавливается после
    возврата API.
  checked: false
  evidence: []
- id: AC-5
  text: Все временные test-owned ресурсы очищены; пользовательский volume и данные
    не затронуты.
  checked: false
  evidence: []
status: in_progress
revision: 2
blockers: []
created_at: '2026-10-19T11:59:34Z'
updated_at: '2026-10-19T12:53:20Z'
next_action: Verify isolated Compose migration-failure gate and record P4 evidence.
progress_note: P1–P3 are integrated; P4 runtime acceptance has started.
---

## Outcome

Изолированный локальный Compose smoke сценарий подтверждает порядок запуска, доступность UI/API, миграцию, создание проекта и его сохранение после перезапуска.

## Scope

Добавить/выполнить воспроизводимые локальные интеграционные проверки через тестовые ресурсы; проверить недоступность DB/API и очистку только принадлежащих тесту ресурсов. Не использовать пользовательские данные и не запускать production/shared сервисы.

## Notes

