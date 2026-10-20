# IMP

IMP.md — индекс фазовых планов. Статусы и гейты принадлежат IMP; реальные задачи и зависимости — task-store. См. [DOCS.md](DOCS.md) и [TODO.md](TODO.md).

## Активные IMP

| Порядок | IMP | Contract source | Цель | Статус | Активная фаза | Зависит от | Блокер | Task package |
|---:|---|---|---|---|---|---|---|---|
| — | Нет активных IMP | — | — | — | — | — | — | — |

## Зарегистрированные пакеты; ожидают зависимостей

IMP-2026-003 развёрнут в TASK-023–TASK-026 и финальную проверку TASK-027. P1 заблокирована условием IMP-BL-01; последующие задачи ждут зависимостей. Все non-terminal Tasks отображаются в [TODO](TODO.md).

## Готовые к разворачиванию

Независимых готовых пакетов нет.

## Заблокированные IMP

| IMP | Затронутая фаза / весь IMP | Основание | Владелец | Условие снятия |
|---|---|---|---|---|
| [IMP-2026-003](docs/plans/imp/imp-2026-003-light-design-system-user-settings.md) | Весь IMP заблокирован P1 / TASK-023; P2–P4 / TASK-024–TASK-026 ждут; финальная TASK-027 | Незакоммиченные frontend и документационные изменения пересекаются с планом | Denis Karmalak / текущий владелец изменений | Checkpoint существующих изменений или отдельный worktree от него |

## Ожидающие финальной проверки

TASK-027 — финальная проверка IMP-2026-003; ждёт завершения TASK-023–TASK-026.

## Недавно завершённые

| IMP | Результат | Фазы | Финальная проверка | Task package |
|---|---|---|---|---|
| [IMP-2026-002](docs/plans/imp/imp-2026-002-domain-workspace.md) | Локальное исследовательское workspace: доступ, рукопись, источники/evidence, mock AI и DOCX export | P1–P8 verified | [TASK-014 accepted](docs/evidence/verification/TASK-014-acceptance.yaml); [finalization](docs/evidence/verification/TASK-014-finalization.yaml); local commits integrated, future/production scope отделён | TASK-006…TASK-014 |
| [imp-2026-001-mvp-foundation](docs/plans/imp/imp-2026-001-mvp-foundation.md) | Локальный MVP: runtime, проекты UI/API и PostgreSQL persistence | P1–P4 verified | Закрыта; Spec, evidence, ограничения и документы сверены | TASK-001…TASK-005 |

## Входящие Spec без готового IMP

Нет.
