# TASK-013 verification evidence

Baseline: `main@12c5b7469bd81182dd82daeabaa3db69b0da4c73`

Task branch: `codex/task-013-citations-export`

## Acceptance evidence

- `tests/integration/test_manuscripts_api.py::test_docx_export_resolves_citations_and_does_not_create_revision` creates a DOCX through the authenticated project API, verifies required OOXML parts, citation/reference numbering, repeated-reference reuse, explicit missing author/year/DOI labels and unchanged manuscript version/revision count.
- `tests/integration/test_manuscripts_api.py::test_docx_export_rejects_missing_citation_source` verifies an unresolved source ID returns HTTP 422 with an actionable error instead of being dropped.
- The manuscript authorization integration test also verifies unauthenticated export returns 401 and a different local user cannot export the owner's project (404).
- The exported DOCX was generated from the converter and successfully opened/converted by LibreOffice 26.2.6.3 to a one-page PDF at `/tmp/paperweave-lo-check/paperweave-export-check.pdf`.
- `frontend/src/editor/Citation.ts` and `ProjectDetailView.vue` persist a citation node with only its source UUID; the source picker uses the current project's owner-scoped source list, and export is disabled while the editor has unsaved changes.
- `src/paperweave/api/manuscripts.py` checks project ownership before reading the manuscript/source list. `docx_export.py` is a pure converter and adds no dependency or persistence write.

## Required checks

| Command | Result |
|---|---|
| `UV_CACHE_DIR=/tmp/paperweave-uv-cache make test` | Passed: 45 tests |
| `npm run typecheck` in `frontend/` | Passed |
| `npm run build` in `frontend/` | Passed; existing Vite warning about runtime-config script and bundle size |
| `python3 -m compileall -q src/paperweave` | Passed |
| `git diff --check` | Passed |
| LibreOffice DOCX to PDF conversion | Passed: one page |

The initial direct pytest attempt lacked `PYTHONPATH=src`; the canonical Compose test target was used. The first sandbox Compose attempt could not write Docker's buildx activity file; the same authorized local test command succeeded with write escalation. Neither preliminary environment failure remains open.

## GitNexus / source fallback

- `analyze --index-only` refreshed the local index for the changed worktree; GitNexus status reports all 234 covered files indexed. The analyzer still reports 15 cross-language field-link skips and truncated candidate flow/callee enumeration.
- `detect-changes --scope all` reported 16 files, 58 symbols, 11 affected flows and an overall `high` aggregate. Specific direct impacts for `render_docx` (LOW; one caller/process), `loadProject` (LOW; one caller) and `downloadManuscriptDocx` (LOW; one caller/process) show no high/critical symbol risk. `export_manuscript_docx` returns `UNKNOWN` upstream because FastAPI route discovery is dynamic; source inspection confirms it is registered through the manuscripts router and directly covered by API tests.
- Because the graph is warning-bearing rather than clean, the fallback reviewed the exact staged source diff, verified ownership checks and pure/no-write export behavior, ran the full 45-test suite plus frontend typecheck/build, compileall, DOCX open/render and whitespace checks. No concrete unresolved data-integrity or authorization risk remains.
