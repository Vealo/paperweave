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

- GitNexus was refreshed after integration and is up-to-date at `main@4704484b92d5077a8e07703b8c96d57a38685be4`, covering all 223 tracked/indexed files. `detect-changes --scope compare --base-ref 0a1659a6ef84f7c4151180258b748a6bf1e6fc1a` reports 35 changed files, 206 symbols, 22 affected processes and aggregate CRITICAL risk. The summary includes changes in documentation plus the new API and shared manuscript-versioning paths; this is an aggregate graph risk, not a confirmed defect. Upstream `ManuscriptService` and `ManuscriptRepository` checks reported LOW exact risk. New endpoint functions have no resolved graph callers (UNKNOWN); route registration and callers were confirmed by source search, API wiring inspection and integration tests.
- The index reports 12 cross-language field links omitted and truncates process enumeration (10 flows at the configured cap, 14 callees at branch cap). Thus freshness is confirmed, but graph coverage is not complete. The pre-commit degraded fallback passed: inspected the manuscript update helper, proposal repository/service/API/UI wiring and direct references; full backend tests, frontend typecheck/build, Python compileall and diff whitespace check passed. Compare-and-swap and proposal decision share one transaction; tests prove stale/accept/reject behavior.
- This evidence does not label GitNexus as a clean or exhaustive analysis and does not establish production network behavior. No unresolved concrete data-integrity defect was found in the reviewed P7 paths.

## Post-integration checks

- `UV_CACHE_DIR=/tmp/paperweave-uv-cache make test` — passed after merge, 43 tests.
- `npm run typecheck && npm run build` (from `frontend/`) — passed after merge, with the same runtime-config and bundle-size advisory warnings noted above.
- `python3 /home/denis/.agents/skills/todo/task-gitflow/scripts/verify_parent_reachability.py --repo /home/denis/Projects/paperweave --parent main --task-commit a464d5bd870158d7519cb61f7ffba43f646bb470` — passed; task commit reachable at parent HEAD `4704484b92d5077a8e07703b8c96d57a38685be4`.
- `node .gitnexus/run.cjs status` — up-to-date at parent HEAD, 223 covered files.
