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
  checked: false
  evidence: []
- id: AC-2
  text: make up в итоговой сводке показывает включённый backend, состояние SeaweedFS,
    S3 endpoint/порт и bucket без вывода credentials; ошибка проверки сообщает причину
    и не заявляет healthy.
  checked: false
  evidence: []
- id: AC-3
  text: make ps и make logs показывают SeaweedFS; make down останавливает его, сохраняя
    persistent volume.
  checked: false
  evidence: []
- id: AC-4
  text: Добавлена отдельная команда проверки S3 health, аутентификации и put/get/delete
    на уникальном тестовом ключе с очисткой; она не читает и не меняет пользовательские
    файлы.
  checked: false
  evidence: []
- id: AC-5
  text: make test или выделенная storage-check проверка использует отдельные test-owned
    ресурсы и проверяет запуск, ожидание готовности и отказ S3.
  checked: false
  evidence: []
- id: AC-6
  text: Runbook описывает порты, конфигурацию и credentials, health checks, команды
    запуска/остановки/логов и безопасную диагностику.
  checked: false
  evidence: []
status: todo
revision: 2
blockers: []
created_at: '2026-10-20T08:29:08Z'
updated_at: '2026-10-20T08:45:34Z'
---

## Outcome

Команды PaperWeave показывают состояние S3-хранилища и позволяют безопасно проверить его локальный запуск и доступность.

## Scope

Makefile, CLI-команды, Compose service health/readiness и runbook для SeaweedFS; не меняет бизнес-API артефактов.

## Notes

The Makefile interface should expose local SeaweedFS startup and a bounded S3 put/get/delete check, then summarize service status without printing secrets.
