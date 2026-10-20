# IMP

IMP.md — индекс фазовых планов. Статусы и гейты принадлежат IMP; реальные задачи и зависимости — task-store. См. [DOCS.md](DOCS.md) и [TODO.md](TODO.md).

## Активные IMP

| Порядок | IMP | Contract source | Цель | Статус | Активная фаза | Зависит от | Блокер | Task package |
|---:|---|---|---|---|---|---|---|---|
| 1 | [IMP-2026-003](docs/plans/imp/imp-2026-003-light-design-system-user-settings.md) | Standalone contract | Единый светлый дизайн-код, устранение конфликта темы и нормализация пользовательских настроек | active | P2 / TASK-024 | TASK-023 verified | — | TASK-023–TASK-027 |

## Зарегистрированные пакеты; ожидают зависимостей

IMP-2026-003 развёрнут в TASK-023–TASK-026 и финальную проверку TASK-027. P1 / TASK-023 verified; IMP-BL-01 снят после checkpoint-коммита `5bed8bfa1966fbf815fbaad0d6cd001215d5dbe5`. P2 / TASK-024 готова к выполнению; последующие задачи ждут зависимостей. Все non-terminal Tasks отображаются в [TODO](TODO.md).

## Готовые к разворачиванию

Независимых готовых пакетов нет.

## Заблокированные IMP

Нет.

## Ожидающие финальной проверки

TASK-027 — финальная проверка IMP-2026-003; ждёт завершения TASK-023–TASK-026.

## Недавно завершённые

| IMP | Результат | Фазы | Финальная проверка | Task package |
|---|---|---|---|---|
| [IMP-2026-002](docs/plans/imp/imp-2026-002-domain-workspace.md) | Локальное исследовательское workspace: доступ, рукопись, источники/evidence, mock AI и DOCX export | P1–P8 verified | [TASK-014 accepted](docs/evidence/verification/TASK-014-acceptance.yaml); [finalization](docs/evidence/verification/TASK-014-finalization.yaml); local commits integrated, future/production scope отделён | TASK-006…TASK-014 |
| [imp-2026-001-mvp-foundation](docs/plans/imp/imp-2026-001-mvp-foundation.md) | Локальный MVP: runtime, проекты UI/API и PostgreSQL persistence | P1–P4 verified | Закрыта; Spec, evidence, ограничения и документы сверены | TASK-001…TASK-005 |

## Входящие Spec без готового IMP

Нет.
