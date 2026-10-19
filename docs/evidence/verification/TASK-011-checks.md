# TASK-011 — проверка реализации

- Revision: ветка `codex/task-011-evidence-claims`, базовый `main@f91c4bd07a808d48e9b936e782b1aff885d5b39a`.
- `UV_CACHE_DIR=/tmp/paperweave-uv-cache make test` — 35 passed; изолированные Compose-контейнеры и сеть удалены.
- `docker build --target ui-build -t paperweave-task-011-ui .` — успешно; production bundle собран.
- `docker run --rm paperweave-task-011-ui npm run typecheck` — успешно (`vue-tsc --noEmit`).
- `python3 -m compileall -q src/paperweave tests` — успешно.
- `git diff --check` — успешно.
- GitNexus index-only refresh завершился успешно; `status` подтвердил актуальность 202/202 покрываемых файлов при `main@f91c4bd` и текущей рабочей копии.
- GitNexus change analysis видит 24 изменённых файла и 47 затронутых flows (`critical`). Индекс сообщает, что 6 deduplicated flows и 11 callees отсечены лимитами, а часть межъязыковых ссылок не строится; граф отмечен как неполный.
- Source fallback: прямой diff подтвердил, что `saveManuscript`/`scheduleSave` не менялись; изменения `ProjectDetailView` ограничены selection locator, переходом к Claim и подключением панели. Все новые API используют `get_current_user` и owner/project-scoped repository queries; миграции, версии, review/retraction и replacement PDF покрыты изолированными integration tests.
- Fallback verdict: passed; конкретного неразрешённого риска по ownership, сохранению файла или invalidation не обнаружено.
- Build сообщает о существующем non-module runtime-config script и bundle больше 500 kB; ошибок сборки нет.
- Проверки локальные; remote/hosted CI не запускался.
