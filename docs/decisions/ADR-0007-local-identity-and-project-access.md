---
schema: adr/v1
id: ADR-0007
name: "Локальная идентификация и доступ к проектам"
type: adr
summary: "Первый срез использует локальный owner-managed provisioning, PostgreSQL server-side sessions и обязательную проверку Project ownership."
version: 1.0.0
status: accepted
freshness: current
last_reviewed: 2026-10-19
date: 2026-10-19
author: Denis Karmalak; decision recorded with Codex
tags: [identity, access-control, local-only, sessions]
decision_kind: security-boundary
decision_owner: Denis Karmalak
supersedes: []
relations:
  roadmaps: [ROADMAP-PAPERWEAVE]
  specs: []
  entities: [ENTITY-PROJECT, ENTITY-USER, ENTITY-SESSION]
  flows: [FLOW-WORKSPACE]
---

# ADR-0007: Локальная идентификация и доступ к проектам

## Контекст

MVP хранил проекты без пользователя и не защищал project API. Дальнейшее развитие требует явного субъекта доступа, срока жизни сессии и безопасной привязки существующих данных. Первая поставка ограничена локальным запуском; удалённый режим и production deployment не утверждены.

## Решение

- PaperWeave работает в режиме local-only. API и UI слушают loopback; PostgreSQL доступен только внутри Compose network.
- Первичный владелец настраивает локальный owner account один раз. После этого только владелец может создавать member accounts. Открытая регистрация, приглашения, self-service password reset и project sharing не входят в этот срез.
- Пароли хранятся как salted PBKDF2-HMAC-SHA256 hashes с 600,000 итерациями; исходные значения не сохраняются.
- Сессии server-side и хранятся в PostgreSQL. Cookie содержит случайный opaque token, база — только его SHA-256 hash. Cookie имеет HttpOnly, SameSite=Strict, host-only scope и путь /api/v1. Так как первый local-only запуск использует HTTP на loopback, флаг Secure выключен.
- Сессия истекает после 12 часов бездействия или через 7 дней после создания — что наступит раньше. Выход удаляет серверную сессию.
- Изменяющие состояние браузерные запросы принимаются только с настроенного loopback UI Origin; CORS разрешает credentials только для loopback UI origins.
- Миграция создаёт зарезервированного passwordless owner с постоянным UUID, назначает ему все существующие проекты и делает projects.owner_id обязательным FK. Первичная настройка единожды заменяет placeholder email/name и задаёт пароль. Новые проекты сразу принадлежат текущему пользователю.
- list, create, get и update всегда ограничены current_user.id; несуществующий или чужой Project возвращает 404.
- Rollback identity migration удаляет identity/session таблицы и owner FK/column, сохраняя содержимое существующих Project rows.

## Последствия

- Несколько локальных аккаунтов изолированы на уровне API. Владельцы могут создавать аккаунты, но просмотр и изменение проектов другим пользователем не допускаются.
- Доверенная граница — локальная машина. Доступ с другого устройства и удалённая публикация не поддерживаются этим решением.
- Локальный администратор с доступом к PostgreSQL может прочитать проектные данные; database encryption at rest и recovery/password reset не обещаются.
- Перед remote/multi-user deployment необходим новый threat model: HTTPS/Secure cookie, CSRF/token policy, origins, recovery, audit, rate limiting и deployment secrets.
- Изменение владельца, reset пароля, удаление учётки и передача проекта потребуют отдельного проверяемого сценария.

## Evidence

- Owner decision: пользователь подтвердил local-only, owner-created accounts, PostgreSQL-backed server-side session with 12-hour idle timeout and 7-day absolute lifetime, and migration of existing projects to the unique owner.
- Implementation and disposable migration evidence: TASK-006.
- Architecture gates: docs/evidence/architecture/imp-2026-002-p1-identity-access.md.
