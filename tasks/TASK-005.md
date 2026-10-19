---
schema: task-store/v1
id: TASK-005
key: IMP-VERIFY:imp-2026-001-mvp-foundation
title: Проверить завершённость MVP и согласованность документации
source_ref: request:2026-10-19-paperweave-mvp-foundation
parent_ref: imp-2026-001-mvp-foundation
phase: null
priority: high
depends_on:
- TASK-001
- TASK-002
- TASK-003
- TASK-004
criteria:
- id: AC-1
  text: Каждый AC Spec и каждый phase gate имеет ссылку на проверяемое source/test/build/runtime
    evidence либо явно указанный пробел.
  checked: true
  evidence:
  - 'docs/plans/imp/imp-2026-001-mvp-foundation.md: Spec AC-1…AC-9 and P1–P4 gates
    mapped to TASK-001…004 evidence'
- id: AC-2
  text: Проверены интеграция P1–P4, архитектурные условия, безопасная персистентность
    и отсутствие включения исключённых функций.
  checked: true
  evidence:
  - tasks/TASK-001.md; tasks/TASK-002.md; tasks/TASK-003.md; tasks/TASK-004.md; docs/decisions/ADR-0006-mvp-boundary.md
- id: AC-3
  text: IMP.md, DOCS.md и TODO.md согласованы с canonical IMP/task store; каждый открытый
    Task отображён ровно в одной категории.
  checked: true
  evidence:
  - tasks validate (14 valid); reconcile-todo.py preview matches TODO.md; IMP.md and
    DOCS.md entries inspected
- id: AC-4
  text: Финальная запись различает локальные проверки и отсутствующие внешние/runtime
    доказательства; IMP закрывается только при выполнении всех обязательных условий.
  checked: true
  evidence:
  - tasks/TASK-005.md Notes; docs/plans/imp/imp-2026-001-mvp-foundation.md limits
    and closed gates
status: done
revision: 2
blockers: []
created_at: '2026-10-19T11:59:51Z'
updated_at: '2026-10-19T14:10:32Z'
progress_note: Повторная сверка подтвердила MVP evidence и согласованность индексов;
  TASK-006 ждёт ACF-1.
---

## Outcome

Независимая финальная проверка сопоставляет реализацию с принятым ADR-0006, критериями draft Spec, фазовыми гейтами и локальными evidence; документирует результат и оставшиеся ограничения.

## Scope

Только проверка завершённых P1–P4, evidence, миграций, изоляции данных, архитектурных условий и связности DOCS/IMP/TODO/task store. Не реализовывать функциональность и не выполнять shared/production эффекты.

## Notes

Recheck requested 2026-10-19 before starting IMP-2026-002: verified the committed MVP reconciliation against the current main baseline. Spec AC-1…AC-9 and P1–P4 gate mappings remain recorded above and refer to TASK-001…004 evidence; current plan continues to report P1–P4 verified and IMP-2026-001 complete. Current task-store validation passes for 14 tasks; TODO projection preview matches the canonical snapshot (1 ready, 10 open) with each open task appearing once; IMP.md and DOCS.md register IMP-2026-002 and keep IMP-2026-001 closed. Local-only evidence boundaries and exclusions remain explicit. No new source/runtime check was needed because this task verifies the already finalized MVP and no MVP implementation files changed since its accepted evidence. TASK-006 remains blocked by owner decision ACF-1; this is outside IMP-2026-001 and does not reopen its closed plan.
