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
  checked: true
  evidence:
  - runtime:paperweave-p3-20261019; DB healthy -> migration completed -> API/UI healthy
    on loopback ports 28741/28742
- id: AC-2
  text: Smoke сценарий создаёт проект через UI/API, останавливает приложение без удаления
    volume, запускает снова и подтверждает наличие проекта.
  checked: true
  evidence:
  - browser created two projects; CLI down/up without -v; same UUIDs remained in GET
    /api/v1/projects
- id: AC-3
  text: При ошибке миграции или недоступности БД приложение не объявляет readiness;
    live остаётся независимым от DB.
  checked: true
  evidence:
  - 'DB outage: live 200 and ready 503; isolated unavailable-host migration failed
    before API/UI containers started'
- id: AC-4
  text: При API outage UI показывает отсутствие соединения и восстанавливается после
    возврата API.
  checked: true
  evidence:
  - browser API stop showed Нет соединения с API; after API restart status returned
    to API доступен
- id: AC-5
  text: Все временные test-owned ресурсы очищены; пользовательский volume и данные
    не затронуты.
  checked: true
  evidence:
  - removed exact test-owned p3/p4/p1 volumes and Compose resources; no matching test
    containers remain
status: done
revision: 3
blockers: []
created_at: '2026-10-19T11:59:34Z'
updated_at: '2026-10-19T12:56:16Z'
progress_note: P4 Compose/browser acceptance passed; restart persistence and failure
  gates verified; test volumes cleaned.
---

## Outcome

Изолированный локальный Compose smoke сценарий подтверждает порядок запуска, доступность UI/API, миграцию, создание проекта и его сохранение после перезапуска.

## Scope

Добавить/выполнить воспроизводимые локальные интеграционные проверки через тестовые ресурсы; проверить недоступность DB/API и очистку только принадлежащих тесту ресурсов. Не использовать пользовательские данные и не запускать production/shared сервисы.

## Notes

Runtime acceptance executed against main source commit 5f5c7f2, with isolated Compose project paperweave-p3-20261019 and /tmp/paperweave-p3.toml (API/UI 28741/28742). DB became healthy, migration completed before API/UI became healthy. Browser created projects 72671ec9-b814-4903-aaff-3b25aaeb1b3b and a35c79d9-d4cf-46a1-8437-1277e3b70e26; both were returned by GET /api/v1/projects after CLI down/up. During DB outage, live returned 200 and ready 503. With a separate test config pointing DB host to unavailable-db-host, CLI up failed in migrate; docker ps -a showed only the healthy DB and no API/UI containers. Browser showed no connection during API stop and API available after restart. Cleanup removed only exact test-owned Compose projects/volumes and verified no matching containers/volumes remained; the earlier P1 test-owned volume was also identity-checked and removed. An initial wrong-password injection was ineffective because Compose initialized the empty test DB with that same password; it was cleaned and replaced with the unavailable-host migration failure probe.
