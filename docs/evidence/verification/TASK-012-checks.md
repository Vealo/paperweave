# TASK-012 verification evidence

Branch: `codex/task-012-ai-proposals`
Base: `main@0a1659a6ef84f7c4151180258b748a6bf1e6fc1a`

## Required checks

- `UV_CACHE_DIR=/tmp/paperweave-uv-cache make test` — passed, 43 tests; test-owned Compose database and network were removed on completion.
- `npm run typecheck` (from `frontend/`) — passed.
- `npm run build` (from `frontend/`) — passed. Existing warnings: `/runtime-config.js` is intentionally not bundled as a module; generated JavaScript chunk is above Vite's 500 kB advisory threshold.
- `python3 -m compileall -q src/paperweave tests` — passed.
- `git diff --check` — passed.

## Criterion evidence

- AC-1: `tests/integration/test_ai_proposals_api.py::test_preview_shows_exact_manifest_and_is_idempotent` verifies the exact manifest in the API response. `frontend/src/components/AIProposalPanel.vue` renders the version, position, selected text, instruction and local mock processing before proposal creation. The production endpoint constructs only `MockLLMAdapter` in `src/paperweave/api/ai_proposals.py`.
- AC-2: integration tests `test_reject_preserves_manuscript_and_decision_is_idempotent` and `test_accept_creates_new_version_and_keeps_original_in_proposal_manifest` verify reject leaves version/content unchanged, accept creates version 2 and original full JSON is available at `/manuscript/versions/1`.
- AC-3: integration tests `test_stale_target_is_marked_and_never_applied`, `test_adapter_timeout_is_explicit_and_does_not_change_manuscript`, and `test_preview_shows_exact_manifest_and_is_idempotent` verify stale rejection, explicit 503 timeout without manuscript mutation, same-key replay and mismatching-key conflict. Accept/reject retries are covered in their respective tests.
- AC-4: API wiring injects only the deterministic local `MockLLMAdapter`; `tests/unit/test_ai_proposal_selection.py` covers selection behavior and the integration suite verifies provider/model metadata and adapter failure handling. No real provider adapter or outbound request is wired in P7. This is a source/test-backed local boundary, not a production network trace.

## Graph and fallback review

- GitNexus status is bound to the base commit `0a1659a`; it does not include this worktree's changes. `detect-changes --scope all` reports 18 changed files, 54 symbols and 11 affected processes, with aggregate HIGH risk. Key upstream checks for `ManuscriptService` and `ManuscriptRepository` report LOW exact risk; the new helper is absent from the base index (`UNKNOWN`), so its direct references were verified with `rg` and inspected in both callers.
- Degraded-analysis fallback: passed. Inspected the manuscript update helper, AI proposal repository/service/API/UI wiring and direct references; ran the full backend tests, frontend typecheck/build, Python compileall, and diff whitespace check. The version compare-and-swap and proposal decision share one transaction, and tests prove stale/accept/reject behavior.
- Graph result remains incomplete and is not represented as a clean graph pass. Refresh and HEAD binding are required after integration.
