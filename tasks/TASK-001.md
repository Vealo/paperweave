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
status: done
revision: 5
blockers: []
created_at: '2026-10-19T11:59:01Z'
updated_at: '2026-10-19T12:25:41Z'
progress_note: All P1 criteria accepted; task commit integrated into main and post-merge
  gates passed.
---

## Outcome

Локальная конфигурация TOML валидируется, а Compose-сервисы запускаются командами проекта с безопасными bind/volume настройками.

## Scope

Реализовать config.toml/config.example.toml, загрузку и проверку настроек, init без перезаписи, launcher и Makefile/Compose lifecycle для локальной среды; не запускать shared/production системы и не удалять данные.

## Notes

## Finalization receipt — 2026-10-19

- Acceptance: TASK-001 AC-1…AC-5 passed; isolated `make test` passed 8 tests.
- Task branch: `codex/task-001-mvp-runtime-config`, based on `main` at `c9f8194`.
- Task commit: `403b3004f935eb76b4dda78583bcc411687770cf` (`feat(TASK-001): add validated local runtime configuration`).
- Parent integration: merge commit `7fea5ffc8086d591a7e4ed8a2ee4abbbe8474d29` on `main`; parent HEAD recorded by reachability verifier; `reachable: true`.
- Post-integration checks: `make test` — 8 passed; plan, phase, IMP contract, task-store and TODO validators passed; `git diff --check` passed.
- Local runtime evidence: `up`, API/UI health, `restart`, `logs`, `migrate`, `down`; temporary project ports loopback-bound, DB has no host port, config mount `RW=false`, named volume survived `down`.
- GitNexus: incomplete/unavailable, not a pass. Post-integration `node .gitnexus/run.cjs analyze` failed writing `/home/denis/.gitnexus/registry.json.tmp...` with `EROFS`; MCP change report observed 16 changed files but zero changed symbols. Pre-commit direct source/reference review, staged diff review, required tests and checks passed; no concrete unresolved P1 safety or data-integrity risk found.
- External actions: no push, hosted CI, PR, or deployment performed.
