---
schema: task-store/v1
id: TASK-010
key: IMP-imp-2026-002-domain-workspace:P5:document-extraction
title: Извлекать фрагменты из документов источников
source_ref: imp-2026-002-domain-workspace#P5
parent_ref: imp-2026-002-domain-workspace
phase: P5
priority: medium
depends_on:
- TASK-009
criteria:
- id: AC-1
  text: Каждый Passage связан с версией файла и версией метода extraction.
  checked: false
  evidence: []
- id: AC-2
  text: Повторная обработка идемпотентна либо создаёт явно новую ExtractionRun; ошибки/partial
    results видимы.
  checked: false
  evidence: []
- id: AC-3
  text: Повреждённый/пустой PDF не теряет оригинал и не создаёт видимость проверенного
    evidence.
  checked: false
  evidence: []
- id: AC-4
  text: При замене файла непереносимый anchor помечается устаревшим для ручной проверки.
  checked: false
  evidence: []
status: todo
revision: 1
blockers: []
created_at: '2026-10-19T14:00:25Z'
updated_at: '2026-10-19T14:00:25Z'
---

## Outcome

PDF источника обрабатывается с provenance, страницами/anchors и отдельным состоянием extraction.

## Scope

После Library определить extraction adapter/version, состояния, retry/partial failure и требование к jobs; связать Passage с конкретной версией SourceFile и показать результат в UI.

## Notes
