---
schema: task-store/v1
id: TASK-018
key: avatar-image-hardening
title: Усилить серверную обработку изображений профиля
source_ref: user:2026-10-20-profile-audit
parent_ref: TASK-015
phase: null
priority: high
depends_on:
- TASK-015
criteria:
- id: AC-1
  text: Сервер независимо проверяет декодируемый формат, размеры изображения и верхний
    предел числа пикселей; MIME и расширению файла не доверяет.
  checked: true
  evidence:
  - tests/unit/test_profile_image_processing.py::test_supported_decoded_images_normalize_to_png_and_ignore_mime;test_dimension_limit_is_enforced_before_storage;test_pixel_limit_is_enforced_at_boundary_before_storage
- id: AC-2
  text: Ориентация нормализована, результат перекодирован в единый поддерживаемый
    формат, EXIF и прочие метаданные удалены.
  checked: true
  evidence:
  - tests/unit/test_profile_image_processing.py::test_exif_orientation_is_applied_and_metadata_is_removed;test_normalized_png_drops_embedded_metadata
- id: AC-3
  text: Новый объект записывается отдельно; указатель БД переключается только после
    успешной обработки и сохранения, а прежний файл удаляется после фиксации.
  checked: true
  evidence:
  - tests/unit/test_profile_image_processing.py::test_supported_decoded_images_normalize_to_png_and_ignore_mime;test_ambiguous_commit_keeps_new_object_when_database_points_to_it;
    code commit 0722358cabbf5d173ba62baaa0f1d24eaf0cc154
- id: AC-4
  text: 'Ошибки проверки/лимита и атомарной записи файла не меняют прежний аватар
    и не оставляют частичного объекта. При ошибке COMMIT сервис сверяет активный ключ
    с PostgreSQL: при подтверждённой новой ссылке сохраняет новый файл и удаляет прежний;
    при подтверждённой старой ссылке удаляет кандидата. Если БД недоступна для сверки,
    сохраняет потенциально используемый файл и пишет структурированное событие; повторяемая
    очистка такого неопределённого объекта выполняется в TASK-020.'
  checked: true
  evidence:
  - tests/unit/test_profile_image_processing.py::test_invalid_or_corrupt_image_does_not_write_or_change_old_object;test_payload_size_limit_is_enforced_before_decode;test_input_exactly_at_byte_limit_is_accepted;test_storage_write_failure_never_updates_database;test_local_avatar_write_failure_leaves_no_partial_or_temporary_object;test_unresolved_commit_outcome_keeps_candidate_and_logs_reconciliation_failure
- id: AC-5
  text: Границы форматов и размеров покрыты изолированными проверками без обращения
    к пользовательской БД или внешнему хранилищу.
  checked: true
  evidence:
  - PYTHONPATH=src UV_CACHE_DIR=/tmp/paperweave-uv-cache uv run --locked --group dev
    pytest tests/unit/test_profile_image_processing.py (16 passed; MemoryRepository,
    MemoryStorage, tmp_path only)
status: done
revision: 7
blockers: []
created_at: '2026-10-20T08:26:00Z'
updated_at: '2026-10-20T09:36:12Z'
progress_note: Normalized image pipeline committed; 16 isolated tests and post-integration
  checks pass
---

## Outcome

Сервер принимает только безопасно декодируемые изображения в заданных пределах и сохраняет нормализованный аватар без исходных метаданных.

## Scope

ProfileService и локальное хранилище аватаров; без интеграции SeaweedFS/S3 и без других типов пользовательских артефактов.

## Notes

This task owns server-side profile image validation and normalization; S3 object lifecycle belongs to TASK-020.

## Finalization evidence

- Local source commit: `0722358cabbf5d173ba62baaa0f1d24eaf0cc154`, reachable from `main` at the same HEAD.
- Post-integration checks: `uv lock --check`; focused isolated avatar suite (16 passed); `compileall`; `git diff HEAD^ HEAD --check`.
- GitNexus refreshed and bound to the commit above. Graph remains incomplete: process tracing capped at 194/220 entry candidates with 46 flows dropped; required source/diff/test fallback passed. No task criterion requires a complete graph.
