---
schema: task-store/v1
id: TASK-022
key: TASK-021:startup-summary-regression
title: Сохранить сводку сервисов при выводе S3 статуса
source_ref: user:2026-10-20-startup-summary-supplement
parent_ref: TASK-021
phase: null
priority: medium
depends_on: []
criteria:
- id: AC-1
  text: После make up и make restart отображаются UI, API, API readiness URL, PostgreSQL,
    миграции и Compose project; затем отдельный вложенный блок хранилища со статусами
    SeaweedFS/S3, endpoint и bucket без credentials, оформленный с одинаковыми отступами
    и выравниванием подписей.
  checked: true
  evidence:
  - 'tests/unit/test_cli.py: 7 passed; mocked up/restart summaries and Compose JSON
    status parser'
  - 'tests/unit/test_cli.py: 7 passed after merge; service summary precedes nested
    storage block for up/restart; git merge f1f512e'
status: done
revision: 6
blockers: []
created_at: '2026-10-20T11:04:00Z'
updated_at: '2026-10-20T11:17:03Z'
progress_note: 'Интегрировано в main; post-merge CLI-проверка: 7 passed; task-store/TODO
  валидны.'
---

## Outcome

Команды make up и make restart показывают исходную сводку состояния PaperWeave и дополняют её сведениями о SeaweedFS/S3.

## Scope

src/paperweave/cli.py startup summary output

## Notes
