---
schema: task-store/v1
id: TASK-011
key: IMP-imp-2026-002-domain-workspace:P6:evidence-claims
title: Связать утверждения рукописи с доказательствами
source_ref: imp-2026-002-domain-workspace#P6
parent_ref: imp-2026-002-domain-workspace
phase: P6
priority: high
depends_on:
- TASK-007
- TASK-010
criteria:
- id: AC-1
  text: Claim и EvidenceLink имеют отдельные identity/lifecycle и ссылаются на конкретные
    версии.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-011-acceptance.yaml
- id: AC-2
  text: supports/contradicts/contextualizes и review status не выводятся из наличия
    цитаты.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-011-acceptance.yaml
- id: AC-3
  text: Изменение Claim/Passage помечает связь на повторную проверку, если её валидность
    устарела.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-011-acceptance.yaml
- id: AC-4
  text: UI различает source citation, extracted passage и проверенное автором evidence.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-011-acceptance.yaml
status: in_progress
revision: 4
blockers: []
created_at: '2026-10-19T14:00:26Z'
updated_at: '2026-10-19T17:47:48Z'
next_action: Подготовить scoped task-коммит и локальную интеграцию в main
progress_note: TASK-011 AC-1–AC-4 приняты; 35 backend тестов и UI build/typecheck
  прошли
---

## Outcome

Автор связывает Claim с SourcePassage типизированным отношением и проверяет связь.

## Scope

Утвердить Claim scope/version, типы relation и ReviewDecision lifecycle; связать Claim с manuscript block и показать навигацию между утверждением, фрагментом и источником.

## Notes

Зафиксированы решения владельца для P6: Claim ограничен утверждением внутри рукописи; собственные/исследовательские результаты автора исключены. В local-only MVP review выполняет единственный владелец проекта; ReviewDecision хранит reviewer, время, решение и заметку. Эти границы уточняют прежний открытый вопрос плана без изменения outcome TASK-011.
