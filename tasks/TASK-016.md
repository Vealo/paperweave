---
schema: task-store/v1
id: TASK-016
key: profile-auth-state
title: Реализовать единое обновление состояния авторизации в интерфейсе
source_ref: user:2026-10-20-profile-audit
parent_ref: TASK-015
phase: null
priority: medium
depends_on:
- TASK-015
criteria:
- id: AC-1
  text: После загрузки приложения пользователь восстанавливается через /auth/me, а
    профиль хранится только в оперативном состоянии клиента.
  checked: true
  evidence:
  - frontend/src/router/index.ts router.beforeEach plus frontend/src/api/auth.ts restoreSession;
    source search confirms no localStorage/sessionStorage state
- id: AC-2
  text: Переходы между защищёнными маршрутами используют единую актуальную проверку
    сессии и не выполняют лишние повторные запросы.
  checked: true
  evidence:
  - frontend/src/api/auth.ts shared sessionRestore and authStatusRestore promises
    plus currentUser in-memory cache; frontend/src/router/index.ts common guard
- id: AC-3
  text: 401, выход и смена пароля очищают состояние; вход и успешное изменение профиля
    обновляют его без перезагрузки.
  checked: true
  evidence:
  - frontend/src/api/projects.ts method-aware 401 dispatch; frontend/src/api/auth.ts
    rememberUser/clearSession/logout/changePassword; frontend/src/App.vue signOut
    finally navigation
- id: AC-4
  text: Возврат по deep link после входа сохраняется; неопределённый/просроченный
    статус не открывает защищённый экран.
  checked: true
  evidence:
  - frontend/src/router/index.ts login next validation and protected-route redirects;
    frontend/src/views/LoginView.vue retry and post-login next handling
status: done
revision: 7
blockers: []
created_at: '2026-10-20T08:25:43Z'
updated_at: '2026-10-20T09:09:05Z'
progress_note: TASK-016 finalized on main at 7fc8a2b; reachability and post-commit
  build passed
---

## Outcome

Состояние текущего пользователя в интерфейсе согласовано с серверной сессией и обновляется по предсказуемой политике.

## Scope

Frontend auth state и router guards; без хранения паролей или токенов в браузерном постоянном хранилище.

## Notes

This follow-up owns frontend session restoration and refresh semantics. Profile CRUD endpoints and profile management screens remain in TASK-015.

## TASK-016 implementation and review (2026-10-20)

- Startup navigation, including `/login` and `/access-denied`, now resolves the shared in-memory session. A valid session restores through `/auth/me`; login redirects authenticated users to a validated local `next` path.
- In-flight session and auth-status requests are shared. Unavailable results are not memoized; LoginView retries availability on mount and exposes a retry action.
- `requestApi` treats only `GET /auth/me` as a restoration probe exempt from global expiry dispatch. Other authenticated endpoint 401s, including `PATCH /auth/me`, dispatch expiry and clear current user state.
- Logout and successful password change clear in-memory state. `App.signOut()` navigates to login even when the server logout request fails and reports that server-side logout could not be confirmed.
- No password, token, or profile state is persisted in localStorage/sessionStorage; profile state is in the `currentUser` Vue ref and restored from `/auth/me`.
- Independent code review confirmed the earlier startup, PATCH-401, logout-failure, and unavailable-retry findings are resolved. Review was source-based; no runtime browser session test was performed.
- `npm run typecheck` and `npm run build` passed. Build reports existing warnings for `/runtime-config.js` and the >500 kB bundle.
- GitNexus index refresh completed for this checkout. Graph analysis warns that the execution-flow enumeration is truncated (186 flows reported, 214 candidates), so graph coverage is incomplete. Staged detect-changes classified the shared requestApi change as critical. The bounded fallback source review, `git diff --cached --check`, typecheck, and production build passed; no concrete unresolved safety issue was found.

## TASK-016 finalization (2026-10-20)

- Scoped implementation and task evidence committed on declared local parent `main`: `7fc8a2b9eb688517e00fd1a51af2f8f5deba1718` (`fix(auth): unify frontend session restoration (TASK-016)`).
- Parent reachability verified: `reachable: true`; parent HEAD equals task commit.
- Post-commit `npm run typecheck` and `npm run build` passed. Existing warnings remain for `/runtime-config.js` script bundling and the >500 kB JS chunk.
- GitNexus refreshed after integration and indexes this HEAD. Its index reports 186 flows from 214 candidates with truncation warnings; do not treat graph coverage as complete. The accepted fallback source review, staged diff review, `git diff --cached --check`, typecheck and build found no unresolved safety issue.
- The working tree still contains the pre-existing unrelated unstaged UI, logging, Compose and documentation changes; they were preserved and excluded from the TASK-016 commit.
