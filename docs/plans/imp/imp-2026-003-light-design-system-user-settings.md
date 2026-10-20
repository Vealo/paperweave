---
schema: imp/v1
id: imp-2026-003-light-design-system-user-settings
name: "Единый светлый дизайн-код и согласование настроек пользователя"
type: imp
version: 1.0.0
status: active
freeze: false
date: 2026-10-20
last_reviewed: 2026-10-20
author: Codex, по пользовательским решениям
tags: [design-system, theme, user-settings, contrast]
contract_mode: standalone
source_ref: Запрос пользователя от 2026-10-20 и подтверждённые решения по палитре и настройкам темы.
spec_ref: null
spec_revision: null
implements:
  requirements: []
baseline_commit: 74901be
relations:
  specs: []
  adrs: [ADR-0007]
  tasks: [TASK-023, TASK-024, TASK-025, TASK-026, TASK-027]
architecture_review:
  required: true
  review_id: imp-2026-003-light-design-system-user-settings
imp_index_ref: IMP.md
verification_task_ref: TASK-027
parent_ref: null
change_kind: none
phases: 4
phase_statuses:
  P1: verified
  P2: active
  P3: pending
  P4: pending
progress: 1/4
analysis_status: complete
analysis_ref: ../../evidence/plan-analysis/imp-2026-003-light-design-system-user-settings.md
architecture_status: complete
architecture_ref: ../../evidence/architecture/imp-2026-003-light-design-system-user-settings.json
finalization_status: pending
audit_ref: null
deployment_mode: not_applicable
---

# Единый светлый дизайн-код и согласование настроек пользователя — Implementation Plan

## Standalone scope contract

**Outcome:** PaperWeave реализует согласованный светлый дизайн-код, не включает неподдерживаемую тёмную схему, сохраняет `light` как единственное значение настройки темы и не смешивает foreground/background разных схем.

**Acceptance criteria:** AC-1 through AC-5 below.

- `AC-1`: палитра централизована в semantic tokens; основные страницы и действия используют согласованные цветовые роли, крупные поверхности остаются нейтральными.
- `AC-2`: после миграции каждая запись `user_settings.theme` и значение по умолчанию равны `light`; API сохраняет поддерживаемое значение и профильный сценарий.
- `AC-3`: визуальное состояние имеет одного владельца; настройки пользователя и запуск приложения не активируют `.p-dark` или системную тёмную схему.
- `AC-4`: header, профиль, формы, карточки, сообщения, полноэкранные диалоги и рабочее пространство проходят проверку сочетаний текста, поверхности и focus.
- `AC-5`: дизайн-код, модель настроек, API и UI описывают одно и то же поведение.

**Non-goals:** Разработка тёмной темы, реакция на `prefers-color-scheme`, новая глобальная система настроек, новый settings store/API/table, изменение идентичности, паролей, сессий, ролей и ownership, изменение поведения полноэкранных диалогов, shared/production миграции, push и deployment.

**Evidence:** локальные frontend/API проверки, disposable PostgreSQL migration rehearsal, сборка UI и ручная визуальная матрица маршрутов/состояний. Успешное выполнение пока не заявляется.

**Source:** Запрос пользователя от 2026-10-20 и подтверждённые решения по палитре и настройкам темы.

## Analysis: child skill result

| Field | Value |
|---|---|
| Child skill | `imp-analysis` |
| Analysis status | complete |
| Analysis artifact | [Analysis](../../evidence/plan-analysis/imp-2026-003-light-design-system-user-settings.md) |
| Analysis verdict | ready_with_blockers |
| Architecture status | complete |
| Architecture artifact | [Architecture control](../../evidence/architecture/imp-2026-003-light-design-system-user-settings.json) |
| Open blocker refs | IMP-BL-01 |

## Audited context

**Contract source:** standalone scope пользователя; черновые Specs не расширяются.
**Analysis artifact:** [imp-2026-003-light-design-system-user-settings.md](../../evidence/plan-analysis/imp-2026-003-light-design-system-user-settings.md)
**Implementation phases:** 4 (нумерация `1..4`; Analysis и Finalization не входят в число фаз).
**Estimated Effort:** не оценивается до исполнения фаз и checkpoint текущего рабочего дерева.

## General requirements and constraints

### Must not change

- Не включать тёмную тему, обработку системной темы ОС или другие цветовые схемы.
- Не менять профили, пароли, сессии, роли, ownership проектов и файлов.
- Не удалять `user_settings`; миграция меняет только `theme`.
- Не менять глобальные правила агентов и чужие/общие окружения.
- Не выполнять shared/production миграции, push или deployment.

### Allowed change surface

- UI: `frontend/src/main.ts`, `frontend/src/App.vue`, `frontend/src/views/ProfileView.vue`, `frontend/src/styles/main.css`, необходимые общие theme tokens/components и тесты.
- Backend/persistence: settings schema/API, `IdentityRepository`, `UserSettingsRecord`, новая Alembic migration и профильные тесты.
- Документы: `docs/design-system.md`, `docs/data-model.md`, этот IMP, `IMP.md`, `DOCS.md` и фазовые evidence.
- Изменять пересекающиеся с текущими dirty-файлы только после снятия IMP-BL-01.

### Compatibility and migrations

- Сохранить таблицу, ключ `user_id` и пользовательскую изоляцию; миграция меняет только `theme`, переводит все текущие значения в `light` и задаёт default `light`.
- На переходе учитывать frontend, который ещё может отправить `system`/`dark`: API не должен допускать рассинхрон между успешным сохранением и применённым состоянием; финальный контракт сохраняет только `light`.
- До миграции локальной пользовательской базы создать snapshot и описать восстановление. Upgrade/downgrade проверять только на disposable PostgreSQL. Откат приложения работает с сохранённым `light`; исходные значения темы восстанавливаются из snapshot, так как пользователь выбрал их нормализацию.
- Другие пользовательские данные и связи миграция не меняет.

### Environment matrix

| Environment | In scope? | Purpose | Required evidence | Mutation authorization |
|---|---|---|---|---|
| local | Yes | Реализация и проверка UI в рабочем приложении | Screenshots, UI flows, settings API | `not_requested` |
| test | Yes | Изолированные PostgreSQL migration/API checks | `make test`, disposable DB evidence | `not_required` |
| ci | No | Hosted pipeline | Отдельный запрос | `not_requested` |
| staging | No | Не задан | — | `not_requested` |
| production | No | Не задан | — | `not_requested` |

**Authorization boundary:** пользователь явно разрешил локальную реализацию IMP. Это разрешение охватывает фазовые локальные изменения и изолированные проверки; оно не разрешает push, deployment, shared/production миграции или изменение внешних окружений.

## Fixed decisions and invariants

| Решение / инвариант | Правило | Последствие |
|---|---|---|
| Активная тема | Только светлая; тёмная тема — отдельная будущая работа | Нельзя включать `.p-dark` или `prefers-color-scheme` |
| Основной акцент | `#5B7917`; тёмное состояние — `#0D3500` | Белый текст допустим на этих двух цветах; крупные поверхности остаются нейтральными |
| Вторичная палитра | `#305700`, `#899D31`, `#B9C24B` — акценты по `docs/design-system.md` | Светлые оттенки не используются как цвет мелкого текста на белом |
| Сохранённое предпочтение | Все существующие и новые значения `theme` — `light` | Миграция обновляет строки; профиль не предлагает неработающие режимы |
| Владелец состояния | PostgreSQL `user_settings` и Identity API остаются источником истины | Не добавлять второе хранилище/API |
| Пересекающиеся изменения | Текущие локальные изменения сохраняются | До checkpoint нельзя править совпадающие файлы |

## Target model

`user_settings` остаётся связанной с `users` один-к-одному; `IdentityRepository` владеет persistence, API — boundary, frontend auth API — транспорт. Сервер хранит `theme = light`; интерфейс всегда активирует светлую схему и не вычисляет её по ОС. App shell отвечает за единое оформление. Профиль отображает личные данные и фиксированную светлую тему. Пункт «Настройки» в header остаётся заглушкой системных настроек и не становится вторым местом выбора пользовательской темы. Поверхности, текст, focus и действия используют shared semantic tokens PrimeVue/Aura и PaperWeave; экраны не задают палитру повторно.

## Work groups and dependency graph

| Group | Purpose | Phases | Outcome |
|---|---|---|---|
| G1 | Shared design foundation | P1 | Семантическая светлая палитра |
| G2 | Durable preference contract | P2 | Мигрированные записи и согласованный API |
| G3 | Runtime and user-facing behavior | P3 | Единый светлый режим и ясные настройки |
| G4 | Whole-surface validation | P4 | Проверенный контраст и согласованные документы |

```text
Checkpoint существующих изменений → P1 → P2 → P3 → P4 → Finalization
```

## Architecture findings and phase gates

| Finding ID | Scope | Phase IDs | Exit condition | Current evidence |
|---|---|---|---|---|
| AC-01 | phases | P1, P3, P4 | Единая светлая политика без второго владельца темы и несовместимых поверхностей. | [Architecture control](../../evidence/architecture/imp-2026-003-light-design-system-user-settings.json) |
| AC-02 | phase | P2 | Миграция, API и старый frontend имеют совместимый переход; восстановление данных описано. | Там же; текущие settings API/schema и migration 0009 |
| AC-03 | phases | P1, P3, P4 | Пересекающиеся изменения checkpointed до редактирования затрагиваемых файлов. | Там же; baseline Git status |

## Phase 1: Реализовать семантическую палитру светлой темы

Phase ID: `P1`; status: `verified` после checkpoint `5bed8bfa1966fbf815fbaad0d6cd001215d5dbe5`, снявшего IMP-BL-01.

### Goal and input

**Goal:** перенести утверждённый дизайн-код в единую реализацию PrimeVue/Aura и общие CSS-токены.
**Inputs:** решения пользователя, `docs/design-system.md`, checkpoint существующих изменений `App.vue`, `main.ts`, `main.css`.

### Preconditions and scope / non-scope

- Preconditions: IMP-BL-01 снят; текущая реализация сверена с checkpoint `5bed8bfa1966fbf815fbaad0d6cd001215d5dbe5`.
- Scope: semantic roles для primary, hover/active, link, focus, selected и нейтральных surface/text/border; применение к PrimeVue controls и общим UI.
- Non-scope: тёмная тема, заливка больших поверхностей цветами палитры, массовый редизайн экранов.

### Affected entities, flows and code

`frontend/src/main.ts`, `frontend/src/styles/main.css`, общие UI-компоненты, `docs/design-system.md`; потоки первичной отрисовки, действий, ссылок, focus и selected.

### Expected result

Основные действия используют `#5B7917`, состояния `hover/active` — `#0D3500`, а большие поверхности остаются нейтральными. Общие компоненты потребляют единые semantic tokens. После фазы можно безопасно остановиться до изменения хранимых настроек.

### Tasks and ownership

**Package Task:** [TASK-023 — Реализовать семантическую палитру светлой темы](../../../tasks/TASK-023.md). Задача `done`; IMP-BL-01 снят указанным checkpoint.

| # | Task | Files / owner | Tests | Status |
|---|---|---|---|---|
| 1.1 | Сверить PrimeVue/Aura public theme API и сопоставить утверждённую палитру с semantic/component tokens. | `main.ts`, frontend | Button/link/focus/selected matrix | `pending` |
| 1.2 | Перевести общие стили на semantic roles; убрать несогласованные цветовые литералы из общих правил. | `styles/main.css`, frontend | Поиск literals + компонентная матрица | `pending` |
| 1.3 | Уточнить дизайн-код так, чтобы документация соответствовала токенам и состояниям. | `docs/design-system.md`, docs owner | Проверка документа и diff | `pending` |

### Data and compatibility

- Нет изменений PostgreSQL/API.
- Не вводить экранные цветовые константы и не переопределять PrimeVue internals вместо публичной настройки.

### Acceptance criteria

- [ ] `AC-P1-001`: основные действия используют `#5B7917` с читаемым текстом.
- [ ] `AC-P1-002`: `#0D3500` ограничен тёмным состоянием акцента; крупные surfaces нейтральны.
- [ ] `AC-P1-003`: общие компоненты используют централизованные semantic tokens.

### Verification

- [ ] `npm --prefix frontend run typecheck`, `npm --prefix frontend run test` и `npm --prefix frontend run build` проходят.
- [ ] Проверены button, link, input, message, focus-visible, selected, disabled и hover/active состояния.
- [ ] Контраст проверяется по выбранным цветовым парам, а не только визуально.

### Evidence contract

| Type | Command/source | Environment | Result | Observed at | Artifact |
|---|---|---|---|---|---|
| `build` | `npm --prefix frontend run build` | `local` | `pass/fail/unavailable` | при исполнении | Task evidence |
| `manual` | Матрица общих компонентов и скриншоты | `local` | `pass/fail/unavailable` | при исполнении | Task evidence |

### Exit criteria

- [ ] Все токены и общие состояния сверены с принятой палитрой.
- [ ] Изменённые файлы происходят из checkpoint; старый и новый diff не смешаны.

## Phase 2: Нормализовать сохранённую настройку темы

Phase ID: `P2`; dependency: P1.

### Goal and input

**Goal:** привести persistent state и HTTP boundary к единственному поддерживаемому значению `light`.
**Inputs:** токен-контракт P1; существующие `user_settings`, API и решение пользователя о миграции.

### Preconditions and scope / non-scope

- Scope: ORM default, API schema/handler, repository, Alembic migration и профильные tests.
- Non-scope: миграция shared/production DB и изменение прочих пользовательских данных.

### Affected entities, flows and code

`UserSettingsRecord`, `UserSettingsUpdateRequest`, `/auth/me/settings`, `IdentityRepository`, новая миграция, settings integration tests.

### Expected result

Существующие и новые записи хранят `light`; переходный API безопасен для старой frontend версии; итоговый контракт принимает только поддерживаемую тему.

### Tasks and ownership

**Package Task:** [TASK-024 — Нормализовать сохранённую настройку темы](../../../tasks/TASK-024.md); depends on TASK-023.

| # | Task | Files / owner | Tests | Status |
|---|---|---|---|---|
| 2.1 | Определить переход API для legacy payload `system`/`dark`, чтобы ответы и DB всегда соответствовали `light`. | schema/API/repository | Legacy и текущий payload/response | `pending` |
| 2.2 | Добавить миграцию backfill: все текущие значения → `light`; default для новых строк → `light`. | migrations, persistence | Disposable DB с прежними значениями и несколькими users | `pending` |
| 2.3 | Зафиксировать финальную валидацию API, default и пользовательскую изоляцию. | models/API/tests | GET/PATCH, invalid values, isolation | `pending` |

### Data and compatibility

- [ ] До миграции локальной пользовательской базы зафиксировать snapshot/restore процедуру.
- [ ] Upgrade/downgrade и повторный upgrade тестировать на disposable PostgreSQL.
- [ ] Downgrade приложения допускает `light`; старые preference values восстанавливаются только из snapshot — их нормализация является согласованным результатом.
- [ ] Проверить, что users, sessions и другие пользовательские данные не меняются.

### Acceptance criteria

- [ ] `AC-P2-001`: все прежние значения `system`, `dark`, `light` приводятся к `light`; новые настройки имеют default `light`.
- [ ] `AC-P2-002`: API читает/сохраняет `light`, сохраняет user isolation и предсказуемо обрабатывает legacy/invalid payload.
- [ ] `AC-P2-003`: migration rehearsal подтверждает отсутствие изменений других пользовательских данных.

### Verification

- [ ] `make test` проходит; integration tests покрывают default, backfill всех вариантов, legacy/invalid payload, авторизацию и изоляцию.
- [ ] Disposable migration upgrade/downgrade проверяет сохранность контрольной выборки.
- [ ] OpenAPI и профильный API contract согласованы.

### Evidence contract

| Type | Command/source | Environment | Result | Observed at | Artifact |
|---|---|---|---|---|---|
| `test` | `make test` (изолированные test DB/SeaweedFS ресурсы) | `test` | `pass/fail/unavailable` | при исполнении | Task evidence |
| `runtime` | Migration upgrade/downgrade cases in `make test` on disposable PostgreSQL | `test` | `pass/fail/unavailable` | при исполнении | Migration evidence |

### Exit criteria

- [ ] Default, migration, API transition и rollback документированы и проверены.
- [ ] Snapshot создан перед любым обновлением живой локальной пользовательской базы.

## Phase 3: Устранить конфликт настроек и активной схемы

Phase ID: `P3`; dependency: P2; precondition: IMP-BL-01 снят.

### Goal and input

**Goal:** убрать конкурирующее применение темы и оставить один источник оформления.
**Inputs:** API response `light`, дизайн-токены P1 и checkpoint frontend baseline.

### Preconditions and scope / non-scope

- Profile показывает зафиксированную тему «Светлая»; `Системная` и `Тёмная` не предлагаются как доступные.
- «Настройки» в account menu остаются заглушкой системных настроек.
- Не удалять settings API/table для сокрытия неподдерживаемой опции.

### Affected entities, flows and code

`App.vue`, `ProfileView.vue`, `main.ts`, при необходимости `auth.ts` и frontend tests. Flow: app bootstrap → settings/profile read/write → visual state.

### Expected result

Приложение остаётся светлым независимо от OS preference, прежних значений и повторного входа; settings API failure не переключает поверхность и не блокирует работу приложения.

### Tasks and ownership

**Package Task:** [TASK-025 — Устранить конфликт настроек и активной схемы](../../../tasks/TASK-025.md); depends on TASK-024.

| # | Task | Files / owner | Tests | Status |
|---|---|---|---|---|
| 3.1 | Удалить дублирующиеся loaders/`applyTheme` и оставить одно владение отображением текущих настроек. | `App.vue`, `ProfileView.vue` | Один bootstrap/update path | `pending` |
| 3.2 | Отключить применение `.p-dark` и `prefers-color-scheme`. | `main.ts`, `App.vue`, styles | Проверить системные light/dark preference | `pending` |
| 3.3 | Убрать недоступный theme selector и разделить личный профиль от системной заглушки. | `ProfileView.vue`, `App.vue` | UI/content/action review | `pending` |

### Data and compatibility

- [ ] Не добавлять localStorage для темы.
- [ ] Logout/login между разными пользователями не переносит профильные поля; видимая схема остаётся светлой.
- [ ] При сбое API ошибка показывается в профиле отдельно; основной shell остаётся читаемым.

### Acceptance criteria

- [ ] `AC-P3-001`: настройки не загружаются/применяются параллельно разными владельцами темы.
- [ ] `AC-P3-002`: ни route transition, ни настройка пользователя/ОС не устанавливают `.p-dark`.
- [ ] `AC-P3-003`: персональная тема не дублируется в системном placeholder menu.

### Verification

- [ ] `npm --prefix frontend run test` покрывает bootstrap, read/save профиля, logout/login и API failure.
- [ ] В браузере с `prefers-color-scheme: dark` прямые загрузки и переходы остаются светлыми.

### Evidence contract

| Type | Command/source | Environment | Result | Observed at | Artifact |
|---|---|---|---|---|---|
| `test` | `npm --prefix frontend run test` | `test` | `pass/fail/unavailable` | при исполнении | Task evidence |
| `manual` | Проверка прямой загрузки, route transitions и профиля | `local` | `pass/fail/unavailable` | при исполнении | Screenshots/checklist |

### Exit criteria

- [ ] Нет альтернативного runtime theme writer/listener.
- [ ] Успешный и ошибочный settings flows не меняют визуальную схему.

## Phase 4: Сквозной аудит контраста и согласованности

Phase ID: `P4`; dependencies: P1–P3.

### Goal and input

**Goal:** проверить дизайн-код на основных страницах и диалогах и согласовать документацию с реализацией.
**Inputs:** verified P1–P3.

### Preconditions and scope / non-scope

- Проверить projects, project workspace, profile, users/new, login/setup, account menu, forms/messages и fullscreen dialogs.
- Не проводить полный редизайн и не разрабатывать тёмную тему.

### Affected entities, flows and code

Общие styles/components, перечисленные маршруты, `docs/design-system.md`, `docs/data-model.md`, `DOCS.md` и evidence.

### Expected result

Основные состояния читаемы при одной светлой схеме; focus видим; документы и UI соответствуют друг другу.

### Tasks and ownership

**Package Task:** [TASK-026 — Провести сквозной аудит контраста и согласованности](../../../tasks/TASK-026.md); depends on TASK-023, TASK-024 and TASK-025.

| # | Task | Files / owner | Tests | Status |
|---|---|---|---|---|
| 4.1 | Составить матрицу экранов, surfaces и states, включая error/disabled/focus. | Frontend/UX | Сверка маршрутов | `pending` |
| 4.2 | Исправить найденные локальные нарушения токенов без изменения поведения функций. | Владельцы UI-компонентов | Повторная проверка тех же состояний | `pending` |
| 4.3 | Согласовать design-system и data-model с фактическим light-only контрактом. | Docs owner | Diff/link check | `pending` |

### Data and compatibility

Нет новых изменений API/schema; документация отражает доказанное поведение фаз P1–P3.

### Acceptance criteria

- [ ] `AC-P4-001`: проверенные экраны не содержат светлой поверхности с белым или низкоконтрастным текстом.
- [ ] `AC-P4-002`: согласие/статус читается и без восприятия оттенка цвета.
- [ ] `AC-P4-003`: design-system, `user_settings`, API и UI не противоречат друг другу.

### Verification

- [ ] Ручная screen matrix включает обычную светлую и тёмную системную настройку ОС.
- [ ] `npm --prefix frontend run typecheck`, `npm --prefix frontend run test`, `npm --prefix frontend run build` и `make test` проходят; baseline failures отделены.
- [ ] `git diff --check` и проектные document/link checks проходят.

### Evidence contract

| Type | Command/source | Environment | Result | Observed at | Artifact |
|---|---|---|---|---|---|
| `manual` | Экранная матрица и скриншоты | `local` | `pass/fail/unavailable` | при исполнении | Verification evidence |
| `test` | `npm --prefix frontend run typecheck`; `npm --prefix frontend run test`; `npm --prefix frontend run build`; `make test` | `local` | `pass/fail/unavailable` | при исполнении | Verification evidence |

### Exit criteria

- [ ] Все перечисленные маршруты проверены; остаточные замечания имеют конкретный blocker/evidence.
- [ ] Документы соответствуют реализованной теме и модели данных.

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Checkpoint изменений `App.vue`, `main.ts`, `main.css` | Baseline | `pending` |
| Migration 0009 и profile settings API | Internal | `available` |
| Disposable PostgreSQL verification | Test | `available` |

## Blockers

| ID | Phase/task | Severity | Status | Evidence | Impact | Owner | Exit condition | Next action |
|---|---|---|---|---|---|---|---|---|
| IMP-BL-01 | P1, затем P2–P4 по зависимостям | `blocking` | `open` | На `main` при HEAD `74901be` изменены без checkpoint `frontend/src/App.vue`, `frontend/src/main.ts`, `frontend/src/styles/main.css`, `docs/design-system.md`, `docs/data-model.md`, `DOCS.md`; все пересекаются с целевой поверхностью. | Риск смешать или затереть существующую пользовательскую работу; зависимые фазы нельзя исполнять в обход P1. | Denis Karmalak / текущий владелец изменений | Изменения checkpointed/integrated или доступен task-owned worktree от их checkpoint. | Сохранить изменения и определить checkpoint до P1. |

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Старый frontend отправляет `system/dark` после обновления API. | Medium | Ошибка профиля или временное расхождение UI/API. | Переходная совместимость до удаления недоступных UI вариантов; проверить старый payload и response. |
| Локальные CSS overrides оставляют несовместимые пары foreground/background. | Medium | Контраст остаётся нарушенным после внедрения палитры. | Семантические токены и визуальная матрица экранов/общих controls. |
| Пересекающиеся незакоммиченные правки смешаются с реализацией. | High | Потеря существующего diff или регрессия. | IMP-BL-01: checkpoint либо отдельный worktree до редактирования. |
| Владелец захочет восстановить прежний выбор темы. | Low | Исходные значения намеренно нормализованы. | Snapshot перед миграцией; точное восстановление только из него. |

## Handoff for another agent

### Ownership map

| Domain | Owner module | May depend on | Must not depend on |
|---|---|---|---|
| Semantic theme | PrimeVue config + shared frontend tokens | `docs/design-system.md` | Screen-level palette literals or dark mode |
| Active appearance | App shell / one settings owner | Identity API `light` response | Duplicate loaders, OS preference, localStorage |
| Durable preference | `user_settings`, Identity API/repository | Existing auth/session boundary | Project ownership or second store |
| Settings UI | ProfileView + system settings placeholder | Shared components/settings API | Duplicated theme selectors |

### Required test matrix

- [ ] PostgreSQL: existing `system/dark/light` rows normalize to `light`; new row defaults to `light`; rollback/snapshot behavior is explicit.
- [ ] API: current-user isolation, transition legacy payload, invalid values, GET after restart.
- [ ] Frontend: bootstrap, profile read/save, logout/login between users, API failure.
- [ ] Visual: light/dark OS preference, key routes, modal/header/forms, focus/disabled/error/consent.

## Finalization audit

`finalization_status` begins `pending`; this audit is not an implementation phase.

### Expected result

Independent evidence confirms all phases, migration behavior, architecture findings, decisions, non-goals and design-code requirements. Separate code completion from local runtime/database evidence; shared/production results remain out of scope.

### Tasks and ownership

**Final verification Task:** [TASK-027 — Провести финальную проверку светлого дизайн-кода и настроек темы](../../../tasks/TASK-027.md); depends on every phase Task.

- Reconcile phase evidence and migration snapshot/restore against implementation and disposable DB checks.
- Reconcile `IMP.md`, `DOCS.md`, design-system and data-model through their owners; reconcile `TODO.md` with the registered TASK-023–TASK-027 package through todo-lifecycle.
- Run plan/reference/diff validation and required GitNexus change analysis during task finalization; degraded graph output must use the documented fallback and never be reported as clean.
- Confirm task-owned changes and phase commits exclude unrelated working-tree changes before closure.

### Audit evidence contract

| Evidence | Source | Required result | Artifact |
|---|---|---|---|
| Phase reconciliation | Canonical IMP and phase evidence | Every mandatory gate supported | Final verification record |
| Local data/UI | Local app and disposable PostgreSQL | Light-only behavior and migration verified | Final verification record |
| Documentation | `IMP.md`, `DOCS.md`, design-system/data-model | Links and claims align with implementation | Final verification record |

## Closure

IMP may become `complete` only after P1–P4 and its final verification Task have accepted evidence, documentation and indices agree, and no mandatory blocker remains. Keep it blocked with exact evidence/resume condition if IMP-BL-01 or a concrete data/API risk remains. If dark theme is later approved, register a successor scope rather than rewriting verified phases.

### Verification

- [ ] Every AC-1…AC-5 maps to verified phase evidence.
- [ ] Migration, compatibility and local restore limits are verified.
- [ ] No hosted/production result is implied by local checks.
- [ ] Register a real final verification Task via task-store before final phase closure.

## Definition of Done

- [ ] Palette implemented centrally through semantic tokens; neutral surfaces and contrast match the accepted design-code.
- [ ] PostgreSQL stores `light` for every user; API behavior is consistent.
- [ ] No application path or OS preference activates `.p-dark`.
- [ ] Profile and system settings have distinct, understandable roles.
- [ ] Automated and visual evidence covers acceptance criteria and failure paths.
- [ ] Docs/indexes reconciled and whole-plan verification accepted.

## Change Log

| Date | Change |
|---|---|
| 2026-10-20 | Initial standalone IMP; implementation blocked until overlapping worktree changes are checkpointed. |
| 2026-10-20 | Expanded into TASK-023–TASK-026 plus final verification TASK-027; P1 remains blocked by IMP-BL-01. |
