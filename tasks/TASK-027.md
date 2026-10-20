---
schema: task-store/v1
id: TASK-027
key: IMP-VERIFY:imp-2026-003-light-design-system-user-settings
title: Провести финальную проверку светлого дизайн-кода и настроек темы
source_ref: docs/plans/imp/imp-2026-003-light-design-system-user-settings.md#finalization-audit
parent_ref: imp-2026-003-light-design-system-user-settings
phase: null
priority: none
depends_on:
- TASK-023
- TASK-024
- TASK-025
- TASK-026
criteria:
- id: AC-1
  text: 'AC-1: Все AC-1…AC-5 и критерии фаз P1–P4 подтверждены относимыми локальными
    или disposable-environment evidence; незакрытые критерии точно перечислены.'
  checked: false
  evidence: []
- id: AC-2
  text: 'AC-2: Миграция и rollback/rehearsal проверены на disposable PostgreSQL, сохранение
    иных пользовательских данных подтверждено, shared/production результат не подразумевается.'
  checked: false
  evidence: []
- id: AC-3
  text: 'AC-3: Архитектурные выводы, non-goals и единственный light-only контракт
    согласованы с кодом, схемой/API/UI и документами.'
  checked: false
  evidence: []
- id: AC-4
  text: 'AC-4: IMP.md, DOCS.md, TODO и ссылки/evidence согласованы с canonical IMP
    и реальными Task ID; проверки плана и ссылок имеют записанные результаты.'
  checked: false
  evidence: []
- id: AC-5
  text: 'AC-5: Task-owned изменения интегрированы в объявленный parent, интеграционные
    ссылки и post-integration checks подтверждены; unrelated dirty baseline не включён.'
  checked: false
  evidence: []
status: in_progress
revision: 3
blockers: []
created_at: '2026-10-20T11:41:34Z'
updated_at: '2026-10-20T13:28:03Z'
next_action: Проверить архитектурные контракты, ссылки и закрыть ветку TASK-027
progress_note: 2 scoped theme migration/API tests passed in disposable PostgreSQL;
  P1/P2 plan checklist reconciled
---

## Outcome

Независимо сверить доказательства всех фаз IMP-2026-003, миграционное поведение, архитектурные ограничения, документацию, индексы и task-owned интеграцию; принять весь план только при выполнении обязательных критериев.

## Scope

Проверить standalone scope contract AC-1…AC-5 и phase AC/evidence P1–P4; сверить архитектурные findings/non-goals и local-only границы; согласовать IMP.md, DOCS.md, TODO links и документы; выполнить plan/reference/diff validation и требуемый GitNexus change analysis с fallback при degraded graph; проверить интеграционные refs и post-integration gates. Не реализовывать feature-код, не выполнять hosted/production действия, не захватывать несвязанные изменения.

## Notes
