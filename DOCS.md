# Реестр документов

Здесь собраны ссылки на канонические документы проекта; содержание хранится в самих документах. Статус задач ведётся в task-store в `tasks/`; очередь первого MVP оформлена в `TODO.md` и `IMP.md`.

## Основные точки входа

| Документ | Назначение | Статус | Когда читать |
|---|---|---|---|
| [README.md](README.md) | Входная точка и текущее состояние реализации | Актуален | При первом знакомстве |
| [docs/vision.md](docs/vision.md) | Цель продукта, принципы, MVP и исключения | Черновик | При обсуждении области продукта |
| [docs/architecture.md](docs/architecture.md) | Целевые границы кода и фактически реализованная узкая основа MVP | Черновик с отмеченным локальным MVP baseline | При обсуждении архитектуры и планировании реализации |
| [docs/design-system.md](docs/design-system.md) | Правила построения UI на готовых компонентах PrimeVue и интеграции Tiptap | Черновик | При разработке экранов, компонентов и стилей frontend |
| [docs/data-model.md](docs/data-model.md) | Целевые сущности и provenance; фактическая project, identity/session и single-manuscript schema | Черновик; схема связана с миграциями | При проектировании модели данных |
| [docs/product-landscape.md](docs/product-landscape.md) | Аналоги и UX-наблюдения из материалов пользователя | Черновик; независимо не проверен | При исследовании продукта |
| [docs/1. Цель MVP.pdf](docs/1.%20Цель%20MVP.pdf) | Исходное описание первого MVP и его acceptance criteria | Материал пользователя | При уточнении или проверке MVP |

## Карта взаимодействий

| Документ | Каноническая область | Статус | Владелец | Когда читать |
|---|---|---|---|---|
| [docs/roadmap.md](docs/roadmap.md) | Предметные области, сущности и целевые взаимодействия исследовательского пространства; не календарь релизов | Черновик | Владелец решения проекта, не указан | При изменении верхнеуровневого сценария |

## ADR

| Документ | Область решения | Статус | Владелец решения | Заменяет |
|---|---|---|---|---|
| [ADR-0001](docs/decisions/ADR-0001-project-identity.md) | Предварительное название продукта и пакета | Предложено | Не указан | — |
| [ADR-0002](docs/decisions/ADR-0002-modular-monolith-and-stack.md) | Модульный монолит, границы модулей и стек | Предложено | Не указан | — |
| [ADR-0003](docs/decisions/ADR-0003-evidence-provenance.md) | Доказательства и их происхождение | Предложено | Не указан | — |
| [ADR-0004](docs/decisions/ADR-0004-author-controlled-ai.md) | Контекстные AI-действия и контроль автора | Принято | Denis Karmalak | — |
| [ADR-0005](docs/decisions/ADR-0005-user-owned-data.md) | Данные пользователя, хранение и передача провайдерам | Принято | Denis Karmalak | — |
| [ADR-0006](docs/decisions/ADR-0006-mvp-boundary.md) | Узкая основа текущего MVP для последующего наращивания отдельными ADR | Принято | Denis Karmalak | — |
| [ADR-0007](docs/decisions/ADR-0007-local-identity-and-project-access.md) | Локальные учётные записи, сессии и ownership проектов | Принято | Denis Karmalak | TASK-006 |
| [ADR-0008](docs/decisions/ADR-0008-citations-and-docx-export.md) | Цитирование и редактируемый DOCX в P8 | Принято | Denis Karmalak | TASK-013 |

## Specs и IMPs

| Документ | Контракт / цель | Статус | Связи |
|---|---|---|---|
| [SPEC-2026-001](docs/specs/spec-2026-001-mvp-foundation.md) | Поведение локального запуска, Projects API/UI и PostgreSQL persistence | Черновик | ADR-0006; IMP-2026-001 |
| [SPEC-2026-002](docs/specs/spec-2026-002-evidence-workflow.md) | Claim рукописи, версии evidence links и review владельцем | Черновик | TASK-011; IMP-2026-002/P6 |
| [SPEC-2026-003](docs/specs/spec-2026-003-ai-proposals.md) | Версионируемые AI-предложения, явный review и mock-only граница передачи данных | Черновик | TASK-012; ADR-0004; ADR-0005; IMP-2026-002/P7 |
| [SPEC-2026-004](docs/specs/spec-2026-004-citations-export.md) | Inline-ссылки на источники проекта и локальный DOCX-экспорт с явными пропусками метаданных | Approved | TASK-013; ADR-0008; IMP-2026-002/P8 |
| [IMP-2026-001](docs/plans/imp/imp-2026-001-mvp-foundation.md) | Фазовая реализация первого MVP; standalone на основе принятого ADR и запроса | Complete; P1–P4 verified, TASK-005 done | TASK-001…TASK-005 |
| [IMP-2026-002](docs/plans/imp/imp-2026-002-domain-workspace.md) | Доменное наращивание локального исследовательского workspace: доступ, рукопись, источники/evidence, mock AI и DOCX | Complete; P1–P8 verified; TASK-014 done | ROADMAP-PAPERWEAVE; пользовательская концепция; IMP-2026-001; [TASK-014 audit](docs/evidence/verification/TASK-014-audit.md); [finalization](docs/evidence/verification/TASK-014-finalization.yaml) |
| [IMP-2026-003](docs/plans/imp/imp-2026-003-light-design-system-user-settings.md) | Единый светлый дизайн-код, устранение конфликта темы и нормализация пользовательских настроек | Blocked before implementation; analysis `ready_with_blockers` | Запрос пользователя 2026-10-20; решения о палитре и переводе значений темы; ADR-0007 |

Полные очереди: [TODO.md](TODO.md) и [IMP.md](IMP.md). Черновой Spec не представлен как утверждённый контракт; scope MVP утверждён ADR-0006.

## Справочные документы

В архитектуре и модели данных отделены целевые предложения от проверенной локальной MVP-основы; обзор аналогов остаётся непроверенным предложением.

| Документ | Каноническая область | Статус | Когда читать |
|---|---|---|---|
| [Хранение пользовательских файлов](docs/storage-artifacts.md) | Реализованный каталог артефактов, типы файлов, storage backends и lifecycle | Локальный контракт; production backup/restore и перенос backend остаются открытыми | При изменении загрузки, замены, удаления или хранения файлов |
| [Логирование PaperWeave](docs/observability/logging.md) | Локальный формат, privacy-ограничения и каталог событий | Применяемый проектный канон | При добавлении логов и диагностике локальных сервисов |

## Runbooks

| Документ | Операция / scope | Когда читать |
|---|---|---|
| [Локальная разработка](docs/runbook-local.md) | Подготовка TOML, команды Makefile, Compose-сервисы, локальный SeaweedFS/S3, изолированные проверки хранилища и просмотр логов | При запуске и обслуживании локального MVP |

## Устаревшие и архивные документы

Нет.
