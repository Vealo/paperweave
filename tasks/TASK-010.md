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
  checked: true
  evidence:
  - docs/evidence/verification/TASK-010-acceptance.yaml#AC-1
- id: AC-2
  text: Повторная обработка идемпотентна либо создаёт явно новую ExtractionRun; ошибки/partial
    results видимы.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-010-acceptance.yaml#AC-2
- id: AC-3
  text: Повреждённый/пустой PDF не теряет оригинал и не создаёт видимость проверенного
    evidence.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-010-acceptance.yaml#AC-3
- id: AC-4
  text: При замене файла непереносимый anchor помечается устаревшим для ручной проверки.
  checked: true
  evidence:
  - docs/evidence/verification/TASK-010-acceptance.yaml#AC-4
status: done
revision: 10
blockers: []
created_at: '2026-10-19T14:00:25Z'
updated_at: '2026-10-19T17:32:13Z'
progress_note: P5 complete on main; all criteria verified and post-integration checks
  passed.
---

## Outcome

PDF источника обрабатывается с provenance, страницами/anchors и отдельным состоянием extraction.

## Scope

После Library определить extraction adapter/version, состояния, retry/partial failure и требование к jobs; связать Passage с конкретной версией SourceFile и показать результат в UI.

## Notes

P5 implementation boundary (2026-10-19): user-approved source input is local PDF only. Use pypdf as an in-process text-layer extractor, with no OCR and no external service; process any language only when extractable text is present. Image-only/scanned or text-empty pages are recorded as empty, not as verified evidence. Persist an ExtractionRun and processor/library version for every explicit attempt; retry creates a new run and preserves earlier runs/passages. Run one file synchronously in the API process (FastAPI sync worker thread); do not add a background queue for this local MVP. Passage anchors remain bound to the exact SourceFile version. When a newer file version is stored, existing references to older versions become needs_review; no automatic anchor transfer is attempted because page/text offsets are not proven portable.
