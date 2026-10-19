# IMP

`IMP.md` — индекс фазовых планов. Статусы и гейты принадлежат IMP; реальные задачи и зависимости — task-store. См. [DOCS.md](DOCS.md) и [TODO.md](TODO.md).

## Активные IMP

| Порядок | IMP | Contract source | Цель | Статус | Готовая фаза | Зависит от | Блокер | Task package |
|---:|---|---|---|---|---|---|---|---|
| 1 | [imp-2026-001-mvp-foundation](docs/plans/imp/imp-2026-001-mvp-foundation.md) | Самостоятельный запрос + ADR-0006 | Локальный запуск, health, проекты и PostgreSQL persistence | active | P2 готова | — | — | TASK-001…TASK-005 |

## Готовые к разворачиванию

Все numbered phases уже развёрнуты в реальные задачи; P1 проверена, P2 готова. Последующие фазы ждут predecessors.

| IMP | Фаза | Предусловия и exit gate | Уже созданные Task |
|---|---|---|---|
| imp-2026-001-mvp-foundation | P2 | TASK-001 integrated; DB/model/API checks | TASK-002 |

## Заблокированные IMP

Нет.

## Ожидающие финальной проверки

Нет; IMP ещё не дошёл до финализации.

## Недавно завершённые

Нет.

## Входящие Spec без готового IMP

Нет.
