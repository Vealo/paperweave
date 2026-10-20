---
schema: task-store/v1
id: TASK-023
key: IMP-2026-003:P1:semantic-light-palette
title: Реализовать семантическую палитру светлой темы
source_ref: docs/plans/imp/imp-2026-003-light-design-system-user-settings.md#phase-1
parent_ref: imp-2026-003-light-design-system-user-settings
phase: P1
priority: none
depends_on: []
criteria:
- id: AC-1
  text: 'AC-P1-001: основные действия используют #5B7917 с читаемым текстом.'
  checked: true
  evidence:
  - 'npm run typecheck/test/build pass; browser primary #5B7917 with white foreground;
    contrast 5.01:1'
- id: AC-2
  text: 'AC-P1-002: #0D3500 ограничен тёмным состоянием акцента; крупные surfaces
    нейтральны.'
  checked: true
  evidence:
  - 'browser hover/active token #0D3500; contrast 13.76:1; accent roles remain controls/state
    and selected surfaces are neutral'
- id: AC-3
  text: 'AC-P1-003: общие компоненты используют централизованные semantic tokens.'
  checked: true
  evidence:
  - 'central --pw-* token set + public Aura definePreset; computed link #305700, focus
    #899D31 at 2px, selected #f4f7ed'
status: done
revision: 5
blockers: []
created_at: '2026-10-20T11:41:12Z'
updated_at: '2026-10-20T12:07:26Z'
progress_note: 'P1: preset и токены внедрены; frontend gates прошли; checkpoint 5bed8bf.'
---

## Outcome

Утвердить и внедрить единую семантическую палитру светлой темы на основе #5B7917 для главных действий и #0D3500 для тёмного состояния акцента, сохранив нейтральные крупные поверхности.

## Scope

После checkpoint IMP-BL-01 сверить PrimeVue/Aura public theme API; централизовать semantic tokens в frontend theme/styles и применить к общим компонентам; синхронизировать docs/design-system.md. Не менять данные/API, не заливать крупные поверхности цветами палитры, не выполнять массовый редизайн и не включать тёмную схему.

## Notes

## Checkpoint and execution start

IMP-BL-01 снят локальным checkpoint commit `5bed8bfa1966fbf815fbaad0d6cd001215d5dbe5` на `main`. Он сохраняет инвентаризированные ранее начатые UI/header/modal, logging/CLI/Compose, storage docs и IMP/TODO/task records; временные `TODO.md.before-reconcile-*` и `tasks/.lock` не включены. Это preservation checkpoint, не приёмка этих функций и не прохождение их проверок. До checkpoint `git diff --check` был чист; task-store валиден (27 задач). Проверка `GitNexus detect_changes` для baseline: 17 changed files, 78 changed symbols, 9 affected flows, risk `high`; затронутые потоки avatar upload, project submission и CLI main просмотрены как ожидаемое следствие накопленного baseline. Обнаруженные изменения в App.vue/main.ts/main.css/design-system/data-model/DOCS теперь закреплены и доступны для сверки.

## Implementation and evidence

Добавлен `frontend/src/theme/paperweavePreset.ts`, который через публичный `definePreset` применяет Aura semantic tokens. Единственный набор цветовых значений находится в начале `frontend/src/styles/main.css`: primary `#5B7917`, hover/active `#0D3500`, link `#305700`, focus/marker `#899D31`, subtle `#B9C24B` и нейтральные selected surfaces. Обновлён `docs/design-system.md` с ролями, правилами применения и контрастом. Текущая dark-mode логика в App shell остаётся незавершённой частью следующей фазы P3 и не считается результатом P1.

Проверки: `npm run typecheck` — pass; `npm run test` — 4 passed; `npm run build` — pass. Build оставил предупреждения runtime-config.js без `type=module` и chunk >500 kB. Контраст, рассчитанный по sRGB: белый на `#5B7917` 5.01:1; белый на `#0D3500` 13.76:1; `#305700` на белом 8.44:1; focus `#899D31` на белом 3.03:1; `#0D3500` на selected surfaces 12.69:1 и 11.57:1.

Ручной браузерный preview `http://127.0.0.1:4173/login`: computed Aura primary `#5B7917`, contrast white, hover `#0D3500`, link `#305700`, focus `#899D31`, selected `#f4f7ed`, `color-scheme: light`; active form field показывает 2px solid focus outline. В screenshot видны нейтральная светлая поверхность и зелёное primary действие. Это локальный Vite preview; API health на `http://127.0.0.1:18741/api/v1/health/live` вернул 200, но preview не получил Compose `runtime-config.js`, поэтому экран показывает ошибку проверки авторизации. Авторизованные маршруты и full-application API flow этим screenshot не подтверждены.
