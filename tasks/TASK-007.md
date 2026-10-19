---
schema: task-store/v1
id: TASK-007
key: IMP-imp-2026-002-domain-workspace:P2:manuscripts
title: Реализовать рукопись и блочное редактирование
source_ref: imp-2026-002-domain-workspace#P2
parent_ref: imp-2026-002-domain-workspace
phase: P2
priority: high
depends_on:
- TASK-006
criteria:
- id: AC-1
  text: Manuscript создаётся и читается в пределах проекта; API возвращает версию
    документа.
  checked: true
  evidence:
  - tests/integration/test_manuscripts_api.py
- id: AC-2
  text: Сериализация блоков проходит round-trip; конкурентный/устаревший save не затирает
    новую версию.
  checked: true
  evidence:
  - tests/integration/test_manuscripts_api.py
- id: AC-3
  text: UI различает dirty/saving/saved/failed и сохраняет введённый текст при сетевой
    ошибке.
  checked: true
  evidence:
  - frontend/src/views/ProjectDetailView.vue
  - docs/evidence/verification/TASK-007-acceptance-ledger.yaml
- id: AC-4
  text: Интеграционная проверка подтверждает сохранность после перезапуска test-owned
    DB.
  checked: true
  evidence:
  - tests/integration/test_manuscripts_api.py
status: done
revision: 6
blockers: []
created_at: '2026-10-19T14:00:25Z'
updated_at: '2026-10-19T15:02:47Z'
progress_note: 'TASK-007 accepted: 25 backend tests and frontend typecheck/build pass
  on integrated main.'
---

## Outcome

Автор создаёт одну рукопись проекта и редактирует упорядоченные блоки через Tiptap с надёжным сохранением.

## Scope

Уточнить контракт single/multiple manuscript, форматы блоков/версий, API сохранения и конфликтов; добавить backend domain/application/API/storage и Tiptap UI в рамках утверждённого Spec.

## Notes
