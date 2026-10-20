---
schema: task-store/v1
id: TASK-019
key: owner-user-creation-ux
title: Доработать форму создания пользовательской учётной записи
source_ref: user:2026-10-20-profile-audit
parent_ref: TASK-015
phase: null
priority: medium
depends_on:
- TASK-017
criteria:
- id: AC-1
  text: Заголовок и идентификация создаваемого пользователя оформлены как шапка страницы,
    поля имени, email и временного пароля сгруппированы в блок «Данные пользователя».
  checked: true
  evidence:
  - frontend/src/views/UsersView.vue (page title, ProfileIdentity, Данные пользователя)
- id: AC-2
  text: До создания явно показано, что выбранный аватар будет загружен после создания
    учётной записи.
  checked: true
  evidence:
  - frontend/src/views/UsersView.vue (conditional upload timing message)
- id: AC-3
  text: Если аккаунт создан, но загрузка аватара не удалась, результат явно сообщает
    частичный успех и позволяет повторить загрузку для того же ID без повторного создания
    аккаунта.
  checked: true
  evidence:
  - frontend/src/views/UsersView.vue and frontend/src/views/user-creation-flow.mjs
    (retain created user ID and retry upload only)
- id: AC-4
  text: Ошибка создания аккаунта сохраняет введённые данные и не сообщает об успешном
    создании.
  checked: true
  evidence:
  - frontend/src/views/UsersView.vue and frontend/tests/user-creation-flow.test.mjs
    (create failure retains form state; no success result)
- id: AC-5
  text: Проверены сценарии без аватара, с успешной загрузкой, с ошибкой загрузки и
    повтором загрузки без дубликата пользователя.
  checked: true
  evidence:
  - frontend/tests/user-creation-flow.test.mjs (4 scenarios pass); npm run typecheck;
    npm run build
status: done
revision: 5
blockers: []
created_at: '2026-10-20T08:26:08Z'
updated_at: '2026-10-20T09:44:48Z'
progress_note: TASK-019 integrated on main; 4 flow tests, typecheck, build, and reachability
  pass
---

## Outcome

Владелец понимает, чью учётную запись создаёт, какие данные вводит и в каком состоянии находится необязательная загрузка аватара.

## Scope

Страница /users/new и её взаимодействие с созданием member-профиля; собственный профиль и изменение пользователей остаются в TASK-015.

## Notes

This task owns the owner-side account creation form after the avatar crop flow from TASK-017; profile editing remains in TASK-015.

TASK-019 implementation integrated locally on main.
Implementation commit: 486a44d5da27dc62961e56c754cefef9817ba288.
Post-integration checks: frontend npm test (4 passed), npm run typecheck (passed), npm run build (passed), git diff --check (passed).
GitNexus staged impact before integration: medium risk; three account-submission execution flows affected. Post-integration index refreshed successfully to current HEAD. Analyzer reports 198 flows and dropped candidates due max-process limits plus 15 cross-language property references; graph is indexed but flow coverage is incomplete.
Independent read-only review found no blocking behavior issue. A stale selected-file label after success was fixed by remounting the picker on form reset.
