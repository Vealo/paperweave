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
  checked: true
  evidence:
  - docs/evidence/verification/TASK-009-acceptance.yaml#AC-1
- id: AC-2
  text: Duplicate/ambiguous записи обрабатываются по явным правилам без потери пользовательских
    данных.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-009-acceptance.yaml#AC-2
- id: AC-3
  text: Загрузка проверяет тип/размер/безопасное имя; файл хранится через storage
    adapter.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-009-acceptance.yaml#AC-3
- id: AC-4
  text: Права проекта ограничивают чтение/скачивание файла; локальная backup/restore
    стратегия документирована.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-009-acceptance.yaml#AC-4
status: done
revision: 5
blockers: []
created_at: '2026-10-19T14:00:25Z'
updated_at: '2026-10-19T16:59:34Z'
progress_note: Completed; 27 post-merge backend tests and both UI checks passed.
---

## Outcome

Автор хранит библиографические записи и исходные файлы в библиотеке проекта с сохранением provenance.

## Scope

Уточнить SourceWork identity/deduplication, метаданные, разрешённые форматы/размеры, storage contract, retention и delete/replace; реализовать API и UI списка/деталей.

## Notes

2026-10-19 owner decision: support manual bibliographic metadata entry and local PDF upload only; no external scholarly lookup or metadata-provider calls. Preserve uploaded file versions while referenced by passages/evidence. Permanent deletion requires an explicit owner action after warning about linked records. Implement version retention and guarded purge semantics against available references; document how future passage/evidence references will be enforced because those domains are not yet implemented.

Finalization evidence (2026-10-19): implementation commit 947198d36f20f8e3378ff49ccd6e98fc17273046 integrated into main by merge 4754833c057918e9d8d0ac37278a388d0fe94563. Parent reachability returned reachable=true. Post-merge isolated backend suite: 27 passed; Vue typecheck and UI production build passed. GitNexus refreshed and status bound to main@4754833; analyzer retained cross-language property warnings for PAPERWEAVE_CONFIG, query and state. Test containers/network were removed.
