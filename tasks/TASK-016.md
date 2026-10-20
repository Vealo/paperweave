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
  checked: false
  evidence: []
- id: AC-2
  text: Переходы между защищёнными маршрутами используют единую актуальную проверку
    сессии и не выполняют лишние повторные запросы.
  checked: false
  evidence: []
- id: AC-3
  text: 401, выход и смена пароля очищают состояние; вход и успешное изменение профиля
    обновляют его без перезагрузки.
  checked: false
  evidence: []
- id: AC-4
  text: Возврат по deep link после входа сохраняется; неопределённый/просроченный
    статус не открывает защищённый экран.
  checked: false
  evidence: []
status: todo
revision: 3
blockers: []
created_at: '2026-10-20T08:25:43Z'
updated_at: '2026-10-20T08:45:33Z'
---

## Outcome

Состояние текущего пользователя в интерфейсе согласовано с серверной сессией и обновляется по предсказуемой политике.

## Scope

Frontend auth state и router guards; без хранения паролей или токенов в браузерном постоянном хранилище.

## Notes

This follow-up owns frontend session restoration and refresh semantics. Profile CRUD endpoints and profile management screens remain in TASK-015.
