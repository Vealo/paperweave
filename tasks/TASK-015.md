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
  checked: false
  evidence:
  - 'tests/integration/test_identity_profiles_api.py: profile GET/PATCH, email reauthentication,
    password reauthentication and session revocation; make test 49 passed.'
- id: AC-2
  text: Владелец может читать список/карточку и обновлять member-профили; создание
    существующего member flow сохраняется.
  checked: false
  evidence:
  - 'tests/integration/test_identity_profiles_api.py: owner list/get/update member,
    member denied, create flow retained; make test 49 passed.'
- id: AC-3
  text: Владелец может мягко деактивировать member-профиль; все его сессии отзываются,
    проекты и пользовательские данные сохраняются; owner нельзя деактивировать.
  checked: false
  evidence:
  - 'tests/integration/test_identity_profiles_api.py: soft deactivation revokes sessions
    and preserves user settings/project; owner deactivation denied; make test 49 passed.'
  - 'tests/integration/test_identity_profiles_api.py: inactive account with stale
    session is rejected on /auth/me and /projects; stale session row is removed; make
    test 50 passed.'
- id: AC-4
  text: Схема включает профильные настройки пользователя с ограниченным контрактом
    и default-row для существующих и новых аккаунтов.
  checked: false
  evidence:
  - 'tests/integration/test_identity_profiles_api.py plus test_alembic_migration_created_the_expected_postgres_schema:
    user_settings defaults/isolation and migration head 20261020_0009; make test 49
    passed.'
- id: AC-5
  text: UI предоставляет текущий профиль и owner-интерфейс управления member-профилями
    с понятными ошибками.
  checked: false
  evidence:
  - ProfileView.vue and UserManagementView.vue implement the requested screens; frontend
    npm run typecheck and npm run build pass.
- id: AC-6
  text: Локальные проверки реализации проходят; diff не содержит несвязанных изменений.
  checked: false
  evidence:
  - 'make test 2026-10-20: isolated Compose DB; 44 passed, 1 failed because schema
    test expected 20261019_0007 while applied head is 20261020_0009; test stack cleaned
    up.'
  - make test 49 passed; npm typecheck/build pass. Full working-tree diff is mixed
    with other tasks and not yet safely isolated.
  - 'make test: 50 passed; npm run typecheck/build passed; Python compileall passed;
    selected task diff staged separately from remaining dirty files.'
status: in_progress
revision: 6
blockers: []
created_at: '2026-10-20T08:16:04Z'
updated_at: '2026-10-20T08:43:57Z'
next_action: Review staged diff, run diff checks, then commit TASK-015 locally.
progress_note: 50 backend tests passed; profile API/UI build verified; task diff is
  selectively staged.
---

## Outcome

Пользовательский профиль и owner-managed профили имеют защищённые операции чтения и изменения; мягкая деактивация отзывает доступ и сохраняет связанные данные.

## Scope

Identity API, модель и миграции PostgreSQL, UI профиля и управления пользователями; сохранение текущих avatar-предпосылок. Без SeaweedFS и внешних эффектов.

## Notes

Ограничения текущего прохода: npm typecheck/build и Python compileall прошли; поведенческие тесты и применение миграции к БД не запускались. Рабочее дерево содержит ранее существовавшие изменения, поэтому scoped commit нельзя безопасно выделить по текущему общему diff.
