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
  checked: false
  evidence: []
- id: AC-2
  text: supports/contradicts/contextualizes и review status не выводятся из наличия
    цитаты.
  checked: false
  evidence: []
- id: AC-3
  text: Изменение Claim/Passage помечает связь на повторную проверку, если её валидность
    устарела.
  checked: false
  evidence: []
- id: AC-4
  text: UI различает source citation, extracted passage и проверенное автором evidence.
  checked: false
  evidence: []
status: todo
revision: 1
blockers: []
created_at: '2026-10-19T14:00:26Z'
updated_at: '2026-10-19T14:00:26Z'
---

## Outcome

Автор связывает Claim с SourcePassage типизированным отношением и проверяет связь.

## Scope

Утвердить Claim scope/version, типы relation и ReviewDecision lifecycle; связать Claim с manuscript block и показать навигацию между утверждением, фрагментом и источником.

## Notes
