---
schema: task-store/v1
id: TASK-001
key: IMP-imp-2026-001-mvp-foundation:P1:local-runtime-config
title: Реализовать конфигурацию и локальный запуск MVP
source_ref: request:2026-10-19-paperweave-mvp-foundation
parent_ref: imp-2026-001-mvp-foundation
phase: P1
priority: high
depends_on: []
criteria:
- id: AC-1
  text: Config-check принимает корректный TOML и с понятной ненулевой ошибкой отвергает
    неверные типы, обязательные поля, порты и таймауты.
  checked: true
  evidence:
  - make config-check with config.example.toml; tests/unit/test_config.py; make test
    (5 passed)
  - make test (8 passed), including missing required field, invalid port and zero
    timeout
- id: AC-2
  text: make init создаёт config.toml только при отсутствии; секреты и DSN не выводятся
    в логи.
  checked: true
  evidence:
  - make init on absent temp path created mode 0600; second init preserved existing
    file; test_invalid_configuration_does_not_echo_password
- id: AC-3
  text: TOML остаётся единственным пользовательским источником конфигурации; Compose
    получает значения через launcher, а config монтируется read-only.
  checked: true
  evidence:
  - docs/runbook-local.md; Compose services mount config read-only; launcher passes
    checked TOML values
- id: AC-4
  text: API/UI host ports по умолчанию loopback-bound, PostgreSQL не опубликован на
    host; make down сохраняет volume.
  checked: true
  evidence:
  - Compose ps showed 127.0.0.1:28741 and :28742; docker inspect DB showed 5432/tcp:null;
    down preserved named volume
- id: AC-5
  text: Определены и работают init, config-check, up, down, restart, logs, ps, migrate,
    test, help с документированной семантикой; ошибка миграции останавливает запуск.
  checked: true
  evidence:
  - make help/test/up/restart/ps/down passed; unit test proves migration failure prevents
    API/UI up; runbook-local.md documents command semantics
  - make logs streamed running services under bounded timeout; make migrate completed;
    make down retained volume
status: in_progress
revision: 4
blockers: []
created_at: '2026-10-19T11:59:01Z'
updated_at: '2026-10-19T12:23:58Z'
next_action: Commit verified P1 and integrate into main
progress_note: 'Final focused suite: 8 passed; command set and isolated Compose lifecycle
  verified.'
---

## Outcome

Локальная конфигурация TOML валидируется, а Compose-сервисы запускаются командами проекта с безопасными bind/volume настройками.

## Scope

Реализовать config.toml/config.example.toml, загрузку и проверку настроек, init без перезаписи, launcher и Makefile/Compose lifecycle для локальной среды; не запускать shared/production системы и не удалять данные.

## Notes

