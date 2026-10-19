# Локальный запуск PaperWeave

Этот runbook относится к локальной разработке. Он не описывает production-развёртывание.

## Подготовка конфигурации

1. Установите Python 3.12+, [`uv`](https://docs.astral.sh/uv/), Node.js 22+, npm, Docker Engine и Docker Compose plugin.
2. Выполните `make init`. Команда копирует `config.example.toml` в `config.toml` с правами владельца `0600` и никогда не перезаписывает существующий файл.
3. Отредактируйте `config.toml`, если заняты порты или нужны другие локальные параметры.
4. Выполните `make config-check`. Ошибки указываются по именам полей; значения паролей и DSN не выводятся.

Приложение читает только TOML. `.env` и `.env.example` не являются его конфигурационным интерфейсом. Launcher отключает автоматический Compose `.env` и передаёт Compose переменные, производные от уже проверенного TOML. Backend и мигратор читают тот же TOML из read-only mount.

## Команды

| Команда | Действие |
|---|---|
| `make help` | Показать цели Makefile; конфигурация не требуется. |
| `make init` | Создать локальный `config.toml`, если его ещё нет. |
| `make config-check` | Разобрать и проверить TOML без вывода секретов. |
| `make up` | Собрать API/UI, запустить PostgreSQL, дождаться readiness БД, выполнить Alembic и только затем запустить API/UI. |
| `make down` | Остановить и удалить контейнеры текущего Compose-проекта; именованный PostgreSQL volume сохраняется. Не добавляйте `-v`. |
| `make restart` | Повторить build/config/migration и пересоздать сервисы с текущими настройками. |
| `make logs` | Следить за последними 100 строками логов Compose-сервисов. |
| `make ps` | Показать состояние сервисов. |
| `make migrate` | Убедиться, что PostgreSQL готов, затем выполнить `alembic upgrade head`. |
| `make test` | Запустить pytest в отдельном Compose-проекте с отдельным PostgreSQL в `tmpfs`; после завершения тестовые контейнеры удаляются. Рабочая БД не подключается. |

Frontend раздаётся через локальный UI-сервис на `http://127.0.0.1:<ui.port>`. SPA загружает `ui.api_base_url` из сгенерированного при старте `runtime-config.js` и обращается к FastAPI напрямую; API разрешает CORS только для настроенного loopback UI-origin. Проверки исходников: `npm --prefix frontend run typecheck` и `npm --prefix frontend run build`.

Путь конфигурации можно переопределить через `PAPERWEAVE_CONFIG=...`, а имя Compose-проекта — через `COMPOSE_PROJECT_NAME=...`, например:

```sh
make config-check PAPERWEAVE_CONFIG=/tmp/paperweave-local.toml
make up COMPOSE_PROJECT_NAME=paperweave-dev
```

Порты по умолчанию: API `127.0.0.1:18741`, UI `127.0.0.1:18742`; PostgreSQL host-порт не публикуется. `deployment.bind_host` принимает только loopback IP. Внутри контейнеров API и UI слушают доступный Compose-интерфейс.

## MVP API

Базовый адрес API — `http://127.0.0.1:18741/api/v1` (порт берётся из `config.toml`). Реализованы:

| Метод и путь | Результат |
|---|---|
| `GET /health/live` | `200`, процесс API запущен; БД не проверяется |
| `GET /health/ready` | `200`, если PostgreSQL доступен, иначе `503` |
| `POST /projects` | Создаёт проект (`201`); `name` после trim — 1–200 символов, `description` — до 5000 |
| `GET /projects` | Возвращает проекты от новых к старым |
| `GET /projects/{uuid}` | Возвращает проект, `404` при отсутствии, `422` для неверного UUID |

Например, создание можно проверить командой `curl -X POST http://127.0.0.1:18741/api/v1/projects -H 'Content-Type: application/json' -d '{"name":"Мой проект","description":"Исследовательский вопрос"}'`. Редактирование, удаление и пагинация в MVP не входят.

## Данные и безопасная остановка

Compose хранит локальную БД в именованном volume `<COMPOSE_PROJECT_NAME>-postgres-data` (для проекта по умолчанию — `paperweave-postgres-data`). `make down` этот volume сохраняет. В MVP нет команды удаления данных. Для временного тестирования используется отдельный service `test-db` с `tmpfs`, без подключения пользовательского volume.

После изменения конфигурации выполните `make restart`. Если конфигурационный файл отсутствует или невалиден, launcher остановится до Compose-команд. Если миграция завершилась ошибкой, API и UI не запускаются.

Значение пароля в `config.example.toml` — только локальная заглушка. Не используйте примерный файл в доступной по сети среде и не помещайте пользовательский `config.toml` в Git.
