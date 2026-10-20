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
  checked: false
  evidence: []
- id: AC-2
  text: 'PostgreSQL является источником истины для каждого объекта: хранит владельца,
    тип/назначение, доменную связь, backend и object key, исходное имя, media type,
    размер, checksum, версию, состояние lifecycle и временные метки; ссылка на объект
    не подменяется публичным URL.'
  checked: false
  evidence: []
- id: AC-3
  text: Аватары, изображения и документы проходят типизированные ограничения; чтение/замена/удаление
    проверяют владельца и доменные ссылки, а credentials и внутренние URL остаются
    только на сервере.
  checked: false
  evidence: []
- id: AC-4
  text: Замена аватара сохраняет и проверяет новый S3-объект, переключает на него
    активную ссылку в PostgreSQL и затем удаляет прежнее изображение; сбой до переключения
    оставляет старый аватар активным, а сбой удаления фиксируется как повторяемое
    состояние очистки. Загрузка и удаление артефактов идемпотентны и не теряют ссылки
    при временной недоступности S3.
  checked: false
  evidence: []
- id: AC-5
  text: Миграция сохраняет существующие записи и локальные файлы; переключение storage
    backend не теряет идентификаторы, версии, checksums и ссылки.
  checked: false
  evidence: []
- id: AC-6
  text: Локальный Compose запускает SeaweedFS с отдельным persistent volume и закрытыми
    credentials; API может проверить доступность выбранного backend.
  checked: false
  evidence: []
- id: AC-7
  text: Изолированные проверки покрывают S3 put/get/delete, ошибку backend, ownership
    и миграцию без доступа к пользовательским файлам или production storage.
  checked: false
  evidence: []
status: todo
revision: 4
blockers: []
created_at: '2026-10-20T08:28:54Z'
updated_at: '2026-10-20T08:45:33Z'
---

## Outcome

PaperWeave хранит типизированные пользовательские файлы через общий storage-интерфейс с локальным SeaweedFS S3 backend и сохраняет метаданные и права доступа в PostgreSQL.

## Scope

Backend storage adapter, Compose для локальной разработки, схема и API пользовательских артефактов типов avatar/image/document; без внешнего deployment, публичных object URL и браузерного прямого доступа к S3.

## Notes

PostgreSQL stores each artifact's object key and lifecycle metadata; replacing an avatar switches the active reference only after the new S3 object is stored, then schedules deletion of the prior object.
