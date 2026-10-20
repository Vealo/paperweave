---
schema: task-store/v1
id: TASK-015
key: profile-crud
title: Реализовать CRUD профилей пользователей
source_ref: user:2026-10-20-profile-crud
parent_ref: null
phase: null
priority: high
depends_on: []
criteria:
- id: AC-1
  text: Аутентифицированный пользователь может читать и обновлять разрешённые поля
    своего профиля; email/password защищены повторной аутентификацией.
  checked: true
  evidence:
  - 'tests/integration/test_identity_profiles_api.py: profile GET/PATCH, email reauthentication,
    password reauthentication and session revocation; make test 49 passed.'
  - 'tests/integration/test_identity_profiles_api.py: profile update, email/password
    reauthentication and session revocation; make test 51 passed (2026-10-20)'
- id: AC-2
  text: Владелец может читать список/карточку и обновлять member-профили; создание
    существующего member flow сохраняется.
  checked: true
  evidence:
  - 'tests/integration/test_identity_profiles_api.py: owner list/get/update member,
    member denied, create flow retained; make test 49 passed.'
  - 'tests/integration/test_identity_profiles_api.py: owner list/get/update/create,
    role restrictions and member denial; make test 51 passed (2026-10-20)'
- id: AC-3
  text: Владелец может мягко деактивировать member-профиль; все его сессии отзываются,
    проекты и пользовательские данные сохраняются; owner нельзя деактивировать.
  checked: true
  evidence:
  - 'tests/integration/test_identity_profiles_api.py: soft deactivation revokes sessions
    and preserves user settings/project; owner deactivation denied; make test 49 passed.'
  - 'tests/integration/test_identity_profiles_api.py: inactive account with stale
    session is rejected on /auth/me and /projects; stale session row is removed; make
    test 50 passed.'
  - 'tests/integration/test_identity_profiles_api.py: soft deactivation, data retention,
    owner denial and stale session rejection; make test 51 passed (2026-10-20)'
- id: AC-4
  text: Схема включает профильные настройки пользователя с ограниченным контрактом
    и default-row для существующих и новых аккаунтов.
  checked: true
  evidence:
  - 'tests/integration/test_identity_profiles_api.py plus test_alembic_migration_created_the_expected_postgres_schema:
    user_settings defaults/isolation and migration head 20261020_0009; make test 49
    passed.'
  - tests/integration/test_projects_api.py:test_user_settings_migration_backfills_existing_accounts
    plus settings defaults/isolation test; make test 51 passed (2026-10-20)
- id: AC-5
  text: UI предоставляет текущий профиль и owner-интерфейс управления member-профилями
    с понятными ошибками.
  checked: true
  evidence:
  - ProfileView.vue and UserManagementView.vue implement the requested screens; frontend
    npm run typecheck and npm run build pass.
  - frontend/src/views/ProfileView.vue, UserManagementView.vue, router/index.ts and
    App.vue route links in 0308e48; npm run typecheck/build passed
- id: AC-6
  text: Локальные проверки реализации проходят; diff не содержит несвязанных изменений.
  checked: true
  evidence:
  - 'make test 2026-10-20: isolated Compose DB; 44 passed, 1 failed because schema
    test expected 20261019_0007 while applied head is 20261020_0009; test stack cleaned
    up.'
  - make test 49 passed; npm typecheck/build pass. Full working-tree diff is mixed
    with other tasks and not yet safely isolated.
  - 'make test: 50 passed; npm run typecheck/build passed; Python compileall passed;
    selected task diff staged separately from remaining dirty files.'
  - Scoped commits 1327d33 and 0308e48; make test 51 passed, frontend typecheck/build
    and Python compileall passed, staged diff checks passed; unrelated dirty files
    excluded
status: done
revision: 7
blockers: []
created_at: '2026-10-20T08:16:04Z'
updated_at: '2026-10-20T08:55:06Z'
progress_note: 51 backend tests, profile UI checks and migration backfill verified;
  commits reachable from main
---

## Outcome

Пользовательский профиль и owner-managed профили имеют защищённые операции чтения и изменения; мягкая деактивация отзывает доступ и сохраняет связанные данные.

## Scope

Identity API, модель и миграции PostgreSQL, UI профиля и управления пользователями; сохранение текущих avatar-предпосылок. Без SeaweedFS и внешних эффектов.

## Notes

Ограничения текущего прохода: npm typecheck/build и Python compileall прошли; поведенческие тесты и применение миграции к БД не запускались. Рабочее дерево содержит ранее существовавшие изменения, поэтому scoped commit нельзя безопасно выделить по текущему общему diff.

## Finalization evidence (2026-10-20)

- `make test`: 51 passed, including an isolated-schema migration test that upgrades an existing user from revision `20261020_0008` to head and confirms default `user_settings` backfill at `20261020_0009`.
- `npm run typecheck` and `npm run build` passed; `python3 -m compileall -q src/paperweave` passed; `git diff --cached --check` passed before each scoped commit.
- Accepted commits on the explicitly requested integration branch `main`: `1327d33048fc16fd4ea7cd8ce3a22d75e311334b` and `0308e4866e864284c97c7cf094898b831f2d3b2d`. Parent reachability verification reported `reachable: true` for both at parent HEAD `0308e4866e864284c97c7cf094898b831f2d3b2d`.
- Navigation to `/profile` and owner `/users` is included as a narrow index-only `App.vue` change. Other pre-existing UI, logging, compose and documentation edits remain unstaged and outside these commits.
- GitNexus staged analysis before the primary commit reported CRITICAL due to `IdentityRepository.resolve_session` fail-closed behavior affecting authenticated flows; that path is intentionally covered by `test_inactive_account_rejects_a_stale_session_on_protected_routes`. The follow-up staged analysis was LOW for the migration test and navigation link. Graph refresh was not run because unrelated working-tree changes remain present; current graph freshness must be treated as not confirmed.
