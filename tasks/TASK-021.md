---
schema: task-store/v1
id: TASK-021
key: seaweedfs-make-ops
title: Добавить команды и сводку запуска SeaweedFS в Makefile
source_ref: user:2026-10-20-seaweedfs-integration; docs/roadmap.md#typed-user-artifacts-s3
parent_ref: TASK-020
phase: null
priority: medium
depends_on:
- TASK-020
criteria:
- id: AC-1
  text: Вызов make без аргументов по-прежнему показывает help; help документирует
    S3-команды и их назначение.
  checked: true
  evidence:
  - make help; Makefile default goal
- id: AC-2
  text: make up в итоговой сводке показывает включённый backend, состояние SeaweedFS,
    S3 endpoint/порт и bucket без вывода credentials; ошибка проверки сообщает причину
    и не заявляет healthy.
  checked: true
  evidence:
  - tests/unit/test_cli.py; make test (84 passed)
  - src/paperweave/cli.py _storage_summary/_run_s3_probe/main; tests/unit/test_cli.py
- id: AC-3
  text: make ps и make logs показывают SeaweedFS; make down останавливает его, сохраняя
    persistent volume.
  checked: true
  evidence:
  - Makefile and compose.yaml service/ps/logs/down configuration
- id: AC-4
  text: Добавлена отдельная команда проверки S3 health, аутентификации и put/get/delete
    на уникальном тестовом ключе с очисткой; она не читает и не меняет пользовательские
    файлы.
  checked: true
  evidence:
  - make storage-check isolated S3 put/get/delete round-trip
- id: AC-5
  text: make test или выделенная storage-check проверка использует отдельные test-owned
    ресурсы и проверяет запуск, ожидание готовности и отказ S3.
  checked: true
  evidence:
  - make test isolated SeaweedFS readiness and 84 passed
- id: AC-6
  text: Runbook описывает порты, конфигурацию и credentials, health checks, команды
    запуска/остановки/логов и безопасную диагностику.
  checked: true
  evidence:
  - docs/runbook-local.md S3 and SeaweedFS operations
status: done
revision: 9
blockers: []
created_at: '2026-10-20T08:29:08Z'
updated_at: '2026-10-20T10:56:46Z'
progress_note: Implemented and integrated on main; isolated S3 check and 84 tests
  passed
---

## Outcome

Команды PaperWeave показывают состояние S3-хранилища и позволяют безопасно проверить его локальный запуск и доступность.

## Scope

Makefile, CLI-команды, Compose service health/readiness и runbook для SeaweedFS; не меняет бизнес-API артефактов.

## Notes

The Makefile interface should expose local SeaweedFS startup and a bounded S3 put/get/delete check, then summarize service status without printing secrets.

Finalization evidence: isolated `make storage-check` completed S3 readiness plus put/get/delete verification; `make test` passed 84 tests and cleaned its test-owned Compose resources. `make up` was not run against the shared/default Compose project; its summary and probe failure behavior are supported by focused CLI unit tests and source review. Reviewer acceptance ledger: /root/audit_task021, accepted AC-1 through AC-6.

Finalization: source commit 59b2aabc23463c677932158124add412da54612b is HEAD on parent main; verify_parent_reachability.py returned reachable=true with parent_head 59b2aabc23463c677932158124add412da54612b. Post-integration GitNexus analyze completed and status reports indexed commit 59b2aab; the analyzer still warns that process-flow coverage is incomplete (214/252 candidates, dropped/truncated entries), so graph is updated but incomplete. Post-integration local checks: make test, 84 passed; make storage-check isolated S3 readiness and round-trip passed. No shared/default `make up` smoke and no push/deploy.
