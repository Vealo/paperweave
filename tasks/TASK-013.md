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
status: in_progress
revision: 5
blockers: []
created_at: '2026-10-19T14:00:26Z'
updated_at: '2026-10-19T19:33:09Z'
progress_note: DOCX export, citations, owner scope, and final local checks verified
approval_state: approved
next_action: Commit verified P8 changes and integrate into main
---

## Outcome

Автор экспортирует рукопись с корректными ссылками на источники в выбранном формате.

## Scope

Утвердить export format, citation style и поведение для неполных метаданных; связать inline citation markers с SourceWork и реализовать export service.

## Notes

P8 format and style approved by Denis Karmalak on 2026-10-19: export editable DOCX; use numeric in-text references in square brackets under ГОСТ Р 7.0.5-2008 and format bibliography descriptions under ГОСТ Р 7.0.100-2018. The latter is the active Russian standard for bibliographic descriptions; ГОСТ Р 7.0.5-2008 governs bibliographic references. Use only manually curated Source metadata; missing fields are marked explicitly and never inferred or fabricated. Export is local and owner-scoped; output must not mutate the manuscript or its saved revisions.
