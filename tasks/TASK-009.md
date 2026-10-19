---
schema: task-store/v1
id: TASK-009
key: IMP-imp-2026-002-domain-workspace:P4:library
title: Добавить библиотеку источников проекта
source_ref: imp-2026-002-domain-workspace#P4
parent_ref: imp-2026-002-domain-workspace
phase: P4
priority: medium
depends_on:
- TASK-006
- TASK-008
criteria:
- id: AC-1
  text: Источник сохраняет стабильный local identity и происхождение метаданных.
  checked: false
  evidence: []
- id: AC-2
  text: Duplicate/ambiguous записи обрабатываются по явным правилам без потери пользовательских
    данных.
  checked: false
  evidence: []
- id: AC-3
  text: Загрузка проверяет тип/размер/безопасное имя; файл хранится через storage
    adapter.
  checked: false
  evidence: []
- id: AC-4
  text: Права проекта ограничивают чтение/скачивание файла; локальная backup/restore
    стратегия документирована.
  checked: false
  evidence: []
status: todo
revision: 1
blockers: []
created_at: '2026-10-19T14:00:25Z'
updated_at: '2026-10-19T14:00:25Z'
---

## Outcome

Автор хранит библиографические записи и исходные файлы в библиотеке проекта с сохранением provenance.

## Scope

Уточнить SourceWork identity/deduplication, метаданные, разрешённые форматы/размеры, storage contract, retention и delete/replace; реализовать API и UI списка/деталей.

## Notes
