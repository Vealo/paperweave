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
  checked: false
  evidence: []
- id: AC-2
  text: make init создаёт config.toml только при отсутствии; секреты и DSN не выводятся
    в логи.
  checked: false
  evidence: []
- id: AC-3
  text: TOML остаётся единственным пользовательским источником конфигурации; Compose
    получает значения через launcher, а config монтируется read-only.
  checked: false
  evidence: []
- id: AC-4
  text: API/UI host ports по умолчанию loopback-bound, PostgreSQL не опубликован на
    host; make down сохраняет volume.
  checked: false
  evidence: []
- id: AC-5
  text: Определены и работают init, config-check, up, down, restart, logs, ps, migrate,
    test, help с документированной семантикой; ошибка миграции останавливает запуск.
  checked: false
  evidence: []
status: todo
revision: 1
blockers: []
created_at: '2026-10-19T11:59:01Z'
updated_at: '2026-10-19T11:59:01Z'
---

## Outcome

Локальная конфигурация TOML валидируется, а Compose-сервисы запускаются командами проекта с безопасными bind/volume настройками.

## Scope

Реализовать config.toml/config.example.toml, загрузку и проверку настроек, init без перезаписи, launcher и Makefile/Compose lifecycle для локальной среды; не запускать shared/production системы и не удалять данные.

## Notes

