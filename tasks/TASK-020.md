---
schema: task-store/v1
id: TASK-020
key: seaweedfs-s3-user-artifacts
title: Интегрировать SeaweedFS как S3-хранилище пользовательских артефактов
source_ref: user:2026-10-20-seaweedfs-integration; docs/roadmap.md#typed-user-artifacts-s3
parent_ref: null
phase: null
priority: high
depends_on:
- TASK-018
criteria:
- id: AC-1
  text: Общий storage-контракт поддерживает локальный backend и S3 backend; SeaweedFS
    выбирается конфигурацией как S3-совместимая реализация, а версия сервиса закреплена.
  checked: true
  evidence:
  - src/paperweave/infrastructure/storage/factory.py; config.example.toml; compose.yaml
    (chrislusf/seaweedfs:4.48)
- id: AC-2
  text: 'PostgreSQL является источником истины для каждого объекта: хранит владельца,
    тип/назначение, доменную связь, backend и object key, исходное имя, media type,
    размер, checksum, версию, состояние lifecycle и временные метки; ссылка на объект
    не подменяется публичным URL.'
  checked: true
  evidence:
  - src/paperweave/infrastructure/db/models.py; migrations/versions/20261020_0010_file_artifacts.py;
    tests/integration/test_library_api.py
- id: AC-3
  text: Аватары, изображения и документы проходят типизированные ограничения; чтение/замена/удаление
    проверяют владельца и доменные ссылки, а credentials и внутренние URL остаются
    только на сервере.
  checked: true
  evidence:
  - src/paperweave/modules/identity/profile.py; src/paperweave/modules/library/service.py;
    tests/integration/test_identity_profiles_api.py; docs/storage-artifacts.md
- id: AC-4
  text: Замена аватара сохраняет и проверяет новый S3-объект, переключает на него
    активную ссылку в PostgreSQL и затем удаляет прежнее изображение; сбой до переключения
    оставляет старый аватар активным, а сбой удаления фиксируется как повторяемое
    состояние очистки. Загрузка и удаление артефактов идемпотентны и не теряют ссылки
    при временной недоступности S3.
  checked: true
  evidence:
  - src/paperweave/infrastructure/db/artifact_lifecycle.py; tests/integration/test_identity_profiles_api.py;
    tests/integration/test_library_api.py
  - tests/integration/test_library_api.py::test_pdf_idempotency_key_maximum_length_fits_catalog
    (119-character request plus 9-character document namespace stores at 128 characters)
  - frontend/src/api/projects.ts::requestApiFormData adds generated Idempotency-Key;
    frontend/src/api/auth.ts callers cover profile and owner avatar uploads; npm test
    (4 passed), npm run typecheck and npm run build succeeded
- id: AC-5
  text: Миграция сохраняет существующие записи и локальные файлы; переключение storage
    backend не теряет идентификаторы, версии, checksums и ссылки.
  checked: true
  evidence:
  - migrations/versions/20261020_0010_file_artifacts.py; tests/integration/test_projects_api.py;
    tests/integration/test_library_api.py
- id: AC-6
  text: Локальный Compose запускает SeaweedFS с отдельным persistent volume и закрытыми
    credentials; API может проверить доступность выбранного backend.
  checked: true
  evidence:
  - 'isolated Compose smoke: DB, SeaweedFS, API, UI healthy; GET /api/v1/health/ready
    returned 200; smoke project cleaned'
- id: AC-7
  text: Изолированные проверки покрывают S3 put/get/delete, ошибку backend, ownership
    и миграцию без доступа к пользовательским файлам или production storage.
  checked: true
  evidence:
  - UV_CACHE_DIR=/tmp/paperweave-uv-cache DOCKER_CONFIG=/tmp/paperweave-docker-config
    BUILDX_CONFIG=/tmp/paperweave-buildx make test (76 passed)
  - UV_CACHE_DIR=/tmp/paperweave-uv-cache DOCKER_CONFIG=/tmp/paperweave-docker-config
    BUILDX_CONFIG=/tmp/paperweave-buildx make test (77 passed, including maximum idempotency-key
    boundary case)
  - UV_CACHE_DIR=/tmp/paperweave-uv-cache DOCKER_CONFIG=/tmp/paperweave-docker-config
    BUILDX_CONFIG=/tmp/paperweave-buildx make test (77 passed); frontend npm test
    (4 passed), typecheck and production build passed
status: done
revision: 11
blockers: []
created_at: '2026-10-20T08:28:54Z'
updated_at: '2026-10-20T10:35:23Z'
progress_note: Committed ba5cbe3 on main; post-commit checks passed; TASK-021 is ready
---

## Outcome

PaperWeave хранит типизированные пользовательские файлы через общий storage-интерфейс с локальным SeaweedFS S3 backend и сохраняет метаданные и права доступа в PostgreSQL.

## Scope

Backend storage adapter, Compose для локальной разработки, схема и API пользовательских артефактов типов avatar/image/document; без внешнего deployment, публичных object URL и браузерного прямого доступа к S3.

## Notes

PostgreSQL stores each artifact's object key and lifecycle metadata; replacing an avatar switches the active reference only after the new S3 object is stored, then schedules deletion of the prior object.

Review repair: retried DELETE accepts active/pending_delete/deleted catalog records for the same owner/type; avatar activation locks the user row; upload endpoints accept Idempotency-Key for avatar/image/PDF, replay same payload, and reject key reuse with changed payload. Added regression cases for image-delete retry and avatar/image/PDF replay. Full isolated `make test` passed (73 passed); focused direct pytest invocation was invalid because integration fixtures require the isolated Compose test-db, then the supported Make target completed successfully.

Final acceptance review (2026-10-20): independent ledger accepted AC-1 through AC-7 for the current source tree. AC-1: configurable local/S3 storage adapters and pinned SeaweedFS image are present in config, storage factory, and Compose. AC-2: `file_artifacts` stores lifecycle and object metadata; migration/backfill and source-parent/idempotency regression checks cover durable references. AC-3: avatar/image/PDF APIs enforce typed validation and owner/domain scope; server-only credentials and non-public object keys are documented and exercised by integration tests. AC-4: avatar replacement switches the PostgreSQL pointer after verified upload; old-object deletion is retryable, and uploads/deletes are idempotent; integration tests cover retries, replacement and replay. AC-5: migration test preserves existing PDF IDs, keys, versions/checksums and registers avatar references without moving file bytes. AC-6: isolated Compose smoke started DB, SeaweedFS, API and UI; `/api/v1/health/ready` returned 200 with database and storage available; smoke resources were removed. AC-7: isolated `make test` passed 76 tests, including S3 adapter, migration, ownership and lifecycle coverage. `compileall` and `git diff --check` passed. This is local verification only; no production deployment was performed.

Acceptance follow-up (2026-10-20): independent audit raised a possible idempotency-key overflow. Source review confirmed the public/document service limit is 119 characters and the `document:` namespace is 9 characters, so the stored value is exactly the PostgreSQL `String(128)` boundary. Added `test_pdf_idempotency_key_maximum_length_fits_catalog`, which exercises a real isolated PostgreSQL upload and asserts a 128-character stored key. Re-ran the supported isolated `make test`: 77 passed in 20.81s. The reported overflow was not present in the reviewed source; the boundary is now regression-tested.

Finalization receipt (2026-10-20): TASK-020 accepted and integrated directly on the user's requested `main` branch as commit `ba5cbe38eaed2ae2343a0b563f3e81d97c8bec3d`. Parent verification: `verify_parent_reachability.py --repo /home/denis/Projects/paperweave --parent main --task-commit ba5cbe38eaed2ae2343a0b563f3e81d97c8bec3d` returned `reachable: true`; parent HEAD equals the task commit. Post-commit checks: isolated `make test` 77 passed; frontend `npm test` 4 passed; `npm run typecheck` passed; `npm run build` succeeded (existing Vite warnings about runtime-config script bundling and chunk size). Isolated SeaweedFS Compose smoke passed earlier: all services healthy and API readiness returned 200; its resources were removed. GitNexus was refreshed and `status` reports indexed commit/current commit `ba5cbe3` and all covered file contents match; analyzer warned that flow coverage is incomplete (211 flows reported; 45 entry candidates and 38 deduplicated flows dropped), so no complete-graph claim is made. No push or deployment was performed.
