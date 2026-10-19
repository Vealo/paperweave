---
schema: task-store/v1
id: TASK-012
key: IMP-imp-2026-002-domain-workspace:P7:ai-assistance
title: Добавить контролируемые AI-предложения
source_ref: imp-2026-002-domain-workspace#P7
parent_ref: imp-2026-002-domain-workspace
phase: P7
priority: medium
depends_on:
- TASK-006
- TASK-007
- TASK-011
criteria:
- id: AC-1
  text: Перед вызовом показан фактически передаваемый контекст и целевая версия.
  checked: false
  evidence: []
- id: AC-2
  text: Reject не меняет рукопись; accept создаёт новую версию, сохраняя исходник.
  checked: false
  evidence: []
- id: AC-3
  text: Timeout/error/stale target обрабатываются явно; повтор не создаёт дублированные
    действия.
  checked: false
  evidence: []
- id: AC-4
  text: Провайдер проверен локальными adapter tests с mock; непредусмотренная передача
    данных отсутствует.
  checked: false
  evidence: []
status: in_progress
revision: 2
blockers: []
created_at: '2026-10-19T14:00:26Z'
updated_at: '2026-10-19T17:53:32Z'
next_action: Зафиксировать решения по контексту, применению предложения и передаче
  данных
progress_note: Зависимости закрыты; решения ADR-0004/0005 и P7 Spec ещё не утверждены
todo_lane: clarification
clarification_question: Утвердить для P7 пользовательский контракт AI и границы передачи
  рукописи провайдеру
clarification_source: ADR-0004, ADR-0005 и Phase 7 в docs/plans/imp/imp-2026-002-domain-workspace.md
---

## Outcome

AI возвращает предложение для явно выбранного контекста, а автор решает применить или отклонить его.

## Scope

После принятия ADR-0004/0005 и отдельного Spec определить context manifest/privacy, LLMService/provider contract и target revision; реализовать preview/accept/reject без скрытой записи в рукопись.

## Notes
