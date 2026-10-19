---
schema: task-store/v1
id: TASK-013
key: IMP-imp-2026-002-domain-workspace:P8:citations-export
title: Подготовить цитирование и экспорт рукописи
source_ref: imp-2026-002-domain-workspace#P8
parent_ref: imp-2026-002-domain-workspace
phase: P8
priority: medium
depends_on:
- TASK-007
- TASK-009
- TASK-011
- TASK-012
criteria:
- id: AC-1
  text: Цитаты разрешаются к источникам; библиография соответствует выбранному стилю/формату.
  checked: false
  evidence: []
- id: AC-2
  text: Неполные метаданные заметно отмечаются и не заменяются вымышленными сведениями.
  checked: false
  evidence: []
- id: AC-3
  text: Golden fixtures/round-trip проверяют структуру экспортированного документа.
  checked: false
  evidence: []
- id: AC-4
  text: Экспорт не меняет сохранённую рукопись и её версии.
  checked: false
  evidence: []
status: todo
revision: 2
blockers: []
created_at: '2026-10-19T14:00:26Z'
updated_at: '2026-10-19T18:24:56Z'
progress_note: P8 reached; export format and citation style await the owner's decision
todo_lane: clarification
clarification_question: Какой формат экспорта и стиль цитирования утвердить для P8?
clarification_source: TASK-013 scope and IMP-2026-002 P8 exit criteria; decision requested
  from Denis Karmalak
---

## Outcome

Автор экспортирует рукопись с корректными ссылками на источники в выбранном формате.

## Scope

Утвердить export format, citation style и поведение для неполных метаданных; связать inline citation markers с SourceWork и реализовать export service.

## Notes
