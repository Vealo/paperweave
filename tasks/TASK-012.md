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
revision: 4
blockers: []
created_at: '2026-10-19T14:00:26Z'
updated_at: '2026-10-19T18:21:32Z'
progress_note: 'P7 acceptance passed: 43 backend tests, frontend typecheck/build,
  compileall; graph fallback documented'
next_action: Commit verified P7 changes, merge into main, run post-integration checks
---

## Outcome

AI возвращает предложение для явно выбранного контекста, а автор решает применить или отклонить его.

## Scope

После принятия ADR-0004/0005 и отдельного Spec определить context manifest/privacy, LLMService/provider contract и target revision; реализовать preview/accept/reject без скрытой записи в рукопись.

## Notes

P7 decisions approved by Denis Karmalak on 2026-10-19: preview/accept/reject over an explicitly selected manuscript block; accept creates a new manuscript version and reject leaves the manuscript unchanged. P7 uses only a deterministic mock LLM adapter; real provider calls and external data transfer are disabled. Before invocation UI shows the exact context manifest. Persist proposal and review metadata for project traceability; do not copy raw prompts/responses into technical logs. See ADR-0004, ADR-0005 and SPEC-2026-003.
