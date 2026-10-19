---
id: spec-2026-003-ai-proposals
name: "Контракт AI-предложений для рукописи"
type: spec
version: 1.0.0
status: draft
freeze: false
date: 2026-10-19
last_reviewed: 2026-10-19
author: Codex, по решениям владельца PaperWeave
tags: [ai, manuscript, proposals, privacy]
depends_on: [spec-2026-001-mvp-foundation]
imp_ref: imp-2026-002-domain-workspace
sources:
  - "TASK-012"
  - "User decisions in Codex, 2026-10-19"
---

# AI-предложения для рукописи

## Границы и решения

P7 поддерживает предложение только для явно выделенного текста одного сохранённого блока рукописи. Пользователь видит текст, target position, целевую версию и instruction/context manifest до запроса. В этом этапе используется только локальный deterministic mock adapter; внешние provider calls и передача данных запрещены. UI помечает результат как демонстрационный mock.

`AIProposal` хранит выбранный manifest, target manuscript/version/position, provider/model metadata, suggestion, lifecycle status и решение владельца. Proposal принадлежит проекту и удаляется вместе с ним. Технические логи содержат только идентификаторы, статус, длительность и код ошибки; raw prompt, selected text и model response в логи не копируются.

## Жизненный цикл

`pending` → `accepted` или `rejected`; при рассогласовании версии — `stale`; ошибка adapter — `failed`. Повтор с тем же idempotency key в пределах проекта возвращает исходный proposal и не вызывает adapter повторно. Повтор key с отличающимся manifest возвращает conflict.

Reject записывает решение reviewer/time/note без изменения manuscript. Accept выполняется только если manuscript version совпадает с target version и исходный selected text всё ещё находится по target position. Accept заменяет выделенный текст предложенным содержимым через новый manuscript version и атомарно фиксирует proposal decision; исходная рукопись остаётся доступна как immutable snapshot через version-history API. Повторный accept идемпотентен.

## API и ошибки

Owner-scoped endpoints: создать предложение, получить предложение, принять или отклонить его. Создание требует `expected_version`, `target_position`, `selected_text`, `instruction`, `idempotency_key`; до adapter call backend проверяет точное совпадение текста и версии. Ответ создания содержит точный persisted manifest, suggestion, provider=`mock`, model=`paperweave-deterministic-mock`, status и timestamps.

`409 stale_target` — изменена версия или текст в locator; `409 idempotency_conflict` — ключ повторён с другим содержимым; `409 already_decided` — несовместимое повторное решение; `422 invalid_selection` — пустой/невалидный selection; provider failure переводит proposal в `failed`, сохраняет исходную рукопись и допускает повтор только с новым idempotency key.

## Проверяемое поведение

- Manifest показывается до вызова и идентичен переданным в adapter полям.
- Mock-only configuration не делает сетевых вызовов и указывает mock в UI/API.
- Adapter timeout/error не меняет manuscript; rejection не меняет manuscript.
- Accept создаёт новую optimistic manuscript version, сохраняя полный исходный JSON snapshot в `manuscript_revisions`; версия читается через owner-scoped API. Stale target отклоняется, один proposal нельзя применить дважды.
- Идемпотентный retry не создаёт дубликат; конфликтующий повтор явно отклоняется.
- Технические логи не содержат raw manifest text, selected text или suggestion.
- Проектные ownership checks действуют на всех endpoints.
