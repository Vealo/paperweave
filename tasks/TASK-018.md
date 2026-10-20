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
  checked: false
  evidence: []
- id: AC-2
  text: Ориентация нормализована, результат перекодирован в единый поддерживаемый
    формат, EXIF и прочие метаданные удалены.
  checked: false
  evidence: []
- id: AC-3
  text: Новый объект записывается отдельно; указатель БД переключается только после
    успешной обработки и сохранения, а прежний файл удаляется после фиксации.
  checked: false
  evidence: []
- id: AC-4
  text: 'Ошибки проверки/лимита и атомарной записи файла не меняют прежний аватар
    и не оставляют частичного объекта. При ошибке COMMIT сервис сверяет активный ключ
    с PostgreSQL: при подтверждённой новой ссылке сохраняет новый файл и удаляет прежний;
    при подтверждённой старой ссылке удаляет кандидата. Если БД недоступна для сверки,
    сохраняет потенциально используемый файл и пишет структурированное событие; повторяемая
    очистка такого неопределённого объекта выполняется в TASK-020.'
  checked: false
  evidence: []
- id: AC-5
  text: Границы форматов и размеров покрыты изолированными проверками без обращения
    к пользовательской БД или внешнему хранилищу.
  checked: false
  evidence: []
status: in_progress
revision: 6
blockers: []
created_at: '2026-10-20T08:26:00Z'
updated_at: '2026-10-20T09:34:08Z'
next_action: Run final focused checks, then commit scoped implementation
progress_note: Commit outcome is reconciled with PostgreSQL; ambiguous references
  are preserved and logged
---

## Outcome

Сервер принимает только безопасно декодируемые изображения в заданных пределах и сохраняет нормализованный аватар без исходных метаданных.

## Scope

ProfileService и локальное хранилище аватаров; без интеграции SeaweedFS/S3 и без других типов пользовательских артефактов.

## Notes

This task owns server-side profile image validation and normalization; S3 object lifecycle belongs to TASK-020.
