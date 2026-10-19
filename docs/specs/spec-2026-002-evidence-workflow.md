---
id: spec-2026-002-evidence-workflow
name: "Контракт утверждений рукописи и проверки evidence"
type: spec
version: 1.0.0
status: draft
freeze: false
date: 2026-10-19
last_reviewed: 2026-10-19
author: Codex, по решениям владельца PaperWeave
tags: [evidence, claims, manuscript, review]
depends_on: [spec-2026-001-mvp-foundation]
imp_ref: imp-2026-002-domain-workspace
sources:
  - "TASK-011"
  - "User decisions in Codex, 2026-10-19"
---

# Утверждения рукописи и review evidence

## Границы

P6 управляет утверждениями, которые автор формулирует в рукописи. Claims
ссылаются на положение блока в конкретной версии Manuscript. Собственные
экспериментальные и иные результаты автора, их атрибуция и хранение не входят
в P6 и требуют отдельного контракта. В local-only MVP единственный владелец
проекта создаёт и проверяет evidence; модель ролей и совместная проверка не
вводятся.

## Сущности и версии

- `Claim` имеет стабильный UUID, текст, позицию блока, `version` и
  `manuscript_version`. Редактирование увеличивает Claim version; Claim связан
  с Manuscript block position и срезом рукописи.
- `EvidenceLink` имеет отдельный UUID/lifecycle и хранит Claim ID/version,
  Passage ID, точный SourceFile ID и manuscript version, relation, rationale и
  `review_state`. Ссылка не означает подтверждение.
- Поддерживаются только `supports`, `contradicts`, `contextualizes`.
- Отвязка переводит связь в `retracted`, сохраняя её identity и историю review;
  новую связь можно создать отдельно.
- Ссылка на Passage удерживает исходную версию файла от удаления.
- Изменение текста Claim или новая версия Manuscript переводит затронутые
  EvidenceLink в `needs_review`. Устаревшую связь нельзя подтвердить без
  повторного review для текущей версии Claim/Manuscript.

## Решения review

Допустимые состояния ссылки: `unreviewed`, `verified`, `rejected`,
`needs_review`, `retracted`. Только явное решение владельца переводит свежую связь в
`verified` или `rejected`. Каждая `ReviewDecision` является append-only записью
с reviewer ID, link version, решением, временем и заметкой. Наличие Citation,
метаданных источника или извлечённого текста не создаёт review decision и не
делает ссылку verified.

## Проверяемое поведение

- UI показывает Claim, отношение, название источника, страницу Passage и
  состояние review раздельно.
- Новое Claim можно создать из выделенного текста рукописи; положение selection
  является locator в зафиксированной manuscript version, а не глобальным ID
  блока.
- Claim связывается только с Passage этого же проекта.
- Создание/изменение Claims и переход review защищены owner session.
- Изменение Claim/Manuscript invalidates старую проверку; stale review возвращает
  конфликт и требует открыть актуальное состояние.
- Отклонённое evidence остаётся видимым с причиной/заметкой; удаление источника
  блокируется, пока на его файл ссылаются passages/evidence.

## Не входит

Внешний scholarly lookup, OCR/AI-интерпретация доказательств, собственные
результаты исследования, соавторство и роли reviewer, цитатные стили и экспорт.
