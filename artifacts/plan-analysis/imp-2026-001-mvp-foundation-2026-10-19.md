# Анализ IMP — imp-2026-001-mvp-foundation: первый MVP PaperWeave

Дата: 2026-10-19. Анализ сделан на baseline `b1ecdc91c41d6cf2f38b74af001d181eeefa6c3e`; в рабочем дереве уже были незакоммиченные документы и каркас. Они сохранены, не трактовались как результат данного анализа.

## Запрос и целевой результат

- Область: зафиксировать MVP из PDF в контракте поведения и создать первую зависимую очередь реализации в task store.
- Репозиторий/ref: `/home/denis/Projects/paperweave`, `main`.
- Наблюдаемый результат: локально запускаемая система; health endpoints; создание и просмотр исследовательских проектов через браузер; PostgreSQL сохраняет данные после остановки/запуска.
- Исключения: PDF, LLM, embeddings/pgvector, background jobs/worker, Tiptap-редактор, auth, совместная работа, production deployment.

## Проверенное текущее состояние

| Область | Вывод | Доказательство | Уверенность |
|---|---|---|---|
| Git baseline | HEAD `b1ecdc9`; множество ранее изменённых/untracked файлов | `git status --short --branch`, `git rev-parse HEAD` | высокая |
| Backend | Есть точки входа-заглушки и пустые пакеты; API/DB сценарии не найдены | `src/paperweave/main.py`, `.gitkeep` в `api`, `modules`, `infrastructure`; `rg --files` | высокая |
| Frontend | Vue entrypoint и пустой App; PrimeVue/Tiptap указаны в package manifest, но инициализация отсутствует | `frontend/src/main.ts`, `App.vue`, `package.json` | высокая |
| Persistence/runtime | Нет миграций, Compose конфигурация ранее создана как scaffold; реализация не подтверждена | `migrations/.gitkeep`, `compose.yaml`, `Dockerfile` (текущий diff) | высокая |
| Tests | Только пустые каталоги unit/integration | `tests/**/.gitkeep` | высокая |
| Canonical task store | Изначально 0 задач, валидный пустой store | `tasks.py list`, `tasks.py validate` | высокая |
| Existing product docs | Vision/roadmap описывают дальний сценарий публикации→evidence→рукопись/AI; ADR-0006 принят владельцем как узкий текущий MVP | `docs/vision.md`, `docs/roadmap.md`, `docs/decisions/ADR-0006-mvp-boundary.md`; прямое решение пользователя 2026-10-19 | высокая |

## Пробелы и влияние

| Пробел | Влияние | Владелец | Требуемая фаза |
|---|---|---|---|
| TOML config validation and Compose launcher отсутствуют | Нельзя получить повторяемый и безопасный локальный запуск | Backend/runtime | P1 |
| PostgreSQL Project model/repository/migration absent | Нет устойчивого источника истины для проектов | Projects + DB adapter | P2 |
| Health/projects endpoints отсутствуют | Нет контракта API для UI и readiness | API | P2 |
| Vue UI отсутствует | Нет пользовательского сквозного сценария | Frontend | P3 |
| Integration checks/startup order unproven | Нельзя подтвердить готовность всей связки и сохранность данных | Runtime/verification | P4 |

## Текущая архитектура и повторно используемые решения

```text
Browser → Vue/PrimeVue/TypeScript → HTTP → FastAPI → Python application scenario → PostgreSQL
Compose owns local service lifecycle; TOML is the single application configuration source.
```

| Граница | Текущий владелец | Переиспользуемый компонент/контракт | Ограничение |
|---|---|---|---|
| UI | `frontend/` | Vite + Vue 3 + PrimeVue 4 + TypeScript manifest | Tiptap исключён из текущего MVP |
| HTTP | `src/paperweave/api/` | FastAPI dependency exists | Routes должны быть тонкими |
| Use case | `src/paperweave/modules/projects/` (через узкий service при нужде) | Project domain folder | Не добавлять абстрактный общий слой без потребности |
| DB/runtime | `infrastructure/db`, `migrations`, Compose | SQLAlchemy/Alembic/PostgreSQL dependencies | Миграции последовательны; `down` сохраняет volume |
| Task status | `tasks/` | Canonical task-store script | TODO только детерминированная проекция |

## Соглашения и ссылки

- Правила: `.agents/AGENTS.md`; глобальная политика `/home/denis/.agents/AGENTS.md`.
- Source scope: `docs/1. Цель MVP.pdf`; более поздний direct user instruction для Vue/PrimeVue/TS и HTTP flow.
- Документы: `docs/architecture.md`, `docs/design-system.md`, `docs/vision.md`, `docs/roadmap.md`, `docs/data-model.md`, ADR-0002 и proposed ADR-0006.
- Стек из manifest: Python >=3.12, FastAPI, Pydantic, SQLAlchemy, psycopg, Alembic; Vue 3, TS, PrimeVue 4, Vite.
- Deployment/CI: вне задачи; локальная Compose-проверка в будущем является частью функционального результата, но запуск сервиса в текущем turn не выполняется.
- Архитектурное заключение: `artifacts/architecture/imp-2026-001-mvp-foundation-2026-10-19.md`.

## Общие требования и ограничения

- Запрещённые пути: `.env`, `.env.*`, secrets/credentials, production data; не копировать пароли в планы/логи.
- Защищённые данные: пользовательская PostgreSQL data volume; миграции только аддитивно для первой схемы, разрушительные операции вне MVP.
- Внешние эффекты: не выполнять push/deploy, не менять общие/production services.
- Изменяемая область реализации: `config*`, `Makefile`, launcher, `compose.yaml`, Dockerfile; `src/paperweave/{api,modules/projects,infrastructure/db}`; `migrations`; `frontend`; `tests`; документация MVP.
- Совместимость: API под `/api/v1`; идентификаторы UUID; UTC timestamp; не использовать NiceGUI или второй config source; `down` не удаляет volume.
- Окружения: local isolated Compose only; CI/shared/staging/production не требуются.

## Решения и открытые вопросы

| Тип | Пункт | Владелец | Основание | Статус |
|---|---|---|---|---|
| Прямое решение пользователя | Текущий MVP — узкая локальная основа для последующего наращивания отдельными ADR; frontend — Vue + PrimeVue 4 + TypeScript, HTTP к FastAPI | Пользователь/владелец проекта | Прямое уточнение пользователя 2026-10-19 | принято; отражено в ADR-0006 |
| Контракт MVP | Проект можно создать/посмотреть; БД сохраняет после restart | Пользовательский PDF | Цель/критерии PDF | фиксировано для draft scope |
| Интерпретация | NiceGUI из PDF заменён Vue, редактор Tiptap не входит в MVP | Пользовательский запрос + PDF | Конфликт стеков разрешён явной хронологией пользовательских указаний | зафиксировано в Spec, не ADR |
| Техническая настройка | Внутренний URL браузерного API должен быть достижим из браузера; контейнерный DNS нельзя выдавать браузеру | Исполнитель задачи | Две отдельные Compose-службы | решить в P3/P4, локальный host gateway/публично настроенный API base URL |

## Блокеры

IMP-wide blockers нет. Технический вопрос URL UI→API не мешает P1/P2; его безопасное решение должно быть определено до интеграционного гейта UI, без изменения внешнего контракта.

## Предлагаемые фазы реализации

| Фаза | Результат | Владелец | Зависимости | Гейт | Deployment |
|---|---|---|---|---|---|
| P1 | TOML validation, local init/launcher, Compose lifecycle and Make commands | Backend/runtime | — | isolated config tests; startup config contract; no secret logs | not applicable |
| P2 | Project schema/repo/API and isolated backend tests | API/Projects/DB | P1 (runtime/config test conventions) | migrations, HTTP contract, persistence integration evidence | not applicable |
| P3 | Vue user flow for health, list/create/detail with PrimeVue | Frontend | P2 API contract | typecheck/build and UI contract evidence | not applicable |
| P4 | Compose end-to-end startup, readiness order, persistence/restart and unavailable dependencies | Runtime/verifier | P1–P3 | local isolated smoke matrix | not applicable |

## Архитектурное заключение

`pass_with_conditions`. Границы UI/API/use case/storage согласованы с модульным монолитом, а источник состояния проектов — PostgreSQL. Условия по фазам: (1) UI не подключается к БД; (2) TOML остаётся единственным пользовательским источником настроек; (3) Compose host ports остаются loopback-bound, DB не публикуется; (4) browser-visible API URL решается до P4; (5) тесты используют отдельную БД/ресурсы; (6) маршруты не содержат бизнес-правила. Это не подтверждение работающего runtime.

## Finalization/closure условия

Финальная verification Task сравнивает все AC Spec и phase gates с исходниками, миграцией, тестами, локальным runtime evidence, TODO/IMP/DOCS и архитектурными условиями. Без подтверждения сохранения данных и изоляции тестовой БД результат не считается завершённым. В текущем анализе сервисы и тесты не запускались.

## Вердикт анализа

`ready`: scope, критерии, исключения, архитектурные границы и доказательства заданы. P1 готова; последующие фазы имеют явные зависимости. Architecture Control: `pass_with_conditions`, условия локализованы по фазам в связанном отчёте. Deployment: `not_applicable`; никаких shared/production mutation не требуется.
