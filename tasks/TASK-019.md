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
  checked: false
  evidence: []
- id: AC-2
  text: До создания явно показано, что выбранный аватар будет загружен после создания
    учётной записи.
  checked: false
  evidence: []
- id: AC-3
  text: Если аккаунт создан, но загрузка аватара не удалась, результат явно сообщает
    частичный успех и позволяет повторить загрузку для того же ID без повторного создания
    аккаунта.
  checked: false
  evidence: []
- id: AC-4
  text: Ошибка создания аккаунта сохраняет введённые данные и не сообщает об успешном
    создании.
  checked: false
  evidence: []
- id: AC-5
  text: Проверены сценарии без аватара, с успешной загрузкой, с ошибкой загрузки и
    повтором загрузки без дубликата пользователя.
  checked: false
  evidence: []
status: todo
revision: 2
blockers: []
created_at: '2026-10-20T08:26:08Z'
updated_at: '2026-10-20T08:45:33Z'
---

## Outcome

Владелец понимает, чью учётную запись создаёт, какие данные вводит и в каком состоянии находится необязательная загрузка аватара.

## Scope

Страница /users/new и её взаимодействие с созданием member-профиля; собственный профиль и изменение пользователей остаются в TASK-015.

## Notes

This task owns the owner-side account creation form after the avatar crop flow from TASK-017; profile editing remains in TASK-015.
