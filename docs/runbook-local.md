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
| `make test` | Запустить pytest в отдельном Compose-проекте с PostgreSQL и SeaweedFS в `tmpfs`; перед pytest проверяется S3 readiness. После завершения тестовые ресурсы удаляются. Рабочая БД и S3 bucket не подключаются. |
| `make storage-check` | Запустить временный изолированный SeaweedFS и проверить bucket, S3-аутентификацию и put/get/delete на уникальном ключе; тестовый bucket и контейнеры удаляются. |

Frontend раздаётся через локальный UI-сервис на `http://127.0.0.1:<ui.port>`. SPA загружает `ui.api_base_url` из сгенерированного при старте `runtime-config.js` и обращается к FastAPI напрямую; API разрешает CORS только для настроенного loopback UI-origin. Проверки исходников: `npm --prefix frontend run typecheck` и `npm --prefix frontend run build`.

Путь конфигурации можно переопределить через `PAPERWEAVE_CONFIG=...`, а имя Compose-проекта — через `COMPOSE_PROJECT_NAME=...`, например:

```sh
make config-check PAPERWEAVE_CONFIG=/tmp/paperweave-local.toml
make up COMPOSE_PROJECT_NAME=paperweave-dev
```

Порты по умолчанию: API `127.0.0.1:18741`, UI `127.0.0.1:18742`; PostgreSQL host-порт не публикуется. `deployment.bind_host` принимает только loopback IP. Внутри контейнеров API и UI слушают доступный Compose-интерфейс.

## S3 и SeaweedFS

Локальный SeaweedFS использует S3 endpoint `http://seaweedfs:8333` внутри Compose-сети; порт `8333` не публикуется на host. Backend, endpoint, bucket и S3 region/key задаются в секции `[storage]` файла `config.toml`. CLI создаёт отдельный SeaweedFS credentials-файл в `.paperweave-secrets/` с правами каталога `0700` и файла `0600`; credentials не передаются в сводку `make up` и не должны попадать в логи или Git. `make up` показывает выбранный backend, endpoint, bucket и состояние сервиса. Для backend `s3` к локальному `seaweedfs` он выполняет ограниченную readiness-проверку bucket/auth; при ошибке пишет код/операцию и завершает команду ненулевым кодом, не помечая storage доступным. При backend `local` внешний S3 endpoint не проверяется.

`make storage-check` создаёт Compose project со случайным именем, отдельным SeaweedFS с данными в `tmpfs` и отдельным bucket. Проверка использует только внутренний endpoint контейнера, ждёт readiness до 30 секунд и выполняет аутентифицированный put/get/delete с проверкой содержимого и удаления. Cleanup удаляет только этот сгенерированный project; пользовательский `paperweave` bucket и его объекты не открываются. `make test` поднимает собственные `test-db` и `storage-check-seaweedfs` в отдельном test project; S3 adapter tests также проверяют ошибочный backend и неуспешные ответы. Обе команды удаляют только test-owned Compose ресурсы при завершении.

Для диагностики используйте `make ps`, `make logs`, затем `make storage-check`. Проверьте, что `config.toml` указывает на доступный S3 endpoint/bucket и что ключи соответствуют credentials; не выводите и не копируйте секреты в issue/log. Если `make storage-check` сообщает `EndpointConnectionError`, проверьте доступность Docker/Compose и дождитесь запуска сервиса; код `AccessDenied`/`InvalidAccessKeyId` указывает на credentials или policy. `make down` останавливает обычные контейнеры и сохраняет именованные PostgreSQL и SeaweedFS volumes; данные можно повторно использовать после `make up`.

## MVP API

Базовый адрес API — `http://127.0.0.1:18741/api/v1` (порт берётся из `config.toml`). При первом открытии UI выполните одноразовую настройку owner account. После этого вход выполняется по email и паролю; owner создаёт остальные локальные аккаунты в разделе «Пользователи». Сессия хранится в PostgreSQL, cookie содержит только случайный token, idle timeout — 12 часов, абсолютный срок — 7 дней. Для сброса базы нет self-service восстановления: повторная настройка owner доступна только после операторского восстановления базы.

Реализованы:

| Метод и путь | Результат |
|---|---|
| `GET /health/live` | `200`, процесс API запущен; БД не проверяется |
| `GET /health/ready` | `200`, если PostgreSQL доступен, иначе `503` |
| `GET /auth/status` | Возвращает, завершена ли первичная настройка owner account |
| `POST /auth/bootstrap` | Однократно создаёт owner account и начинает сессию (`201`) |
| `POST /auth/login`, `POST /auth/logout`, `GET /auth/me` | Вход, выход и сведения о текущем пользователе |
| `POST /auth/users` | Создаёт member account; доступно только owner (`201`) |
| `POST /projects` | Создаёт проект текущего пользователя (`201`); `name` после trim — 1–200 символов, `description` — до 5000 |
| `GET /projects` | Возвращает только проекты текущего пользователя от новых к старым |
| `GET /projects/{uuid}` | Возвращает только принадлежащий пользователю проект; иначе `404` |
| `PUT /projects/{uuid}` | Обновляет только принадлежащий пользователю проект; иначе `404` |

Браузерные операции используют credentials cookie и должны приходить с настроенного loopback UI Origin. Редактирование проекта доступно; удаление и пагинация в MVP не входят.

## Данные и безопасная остановка

Compose хранит локальную БД в именованном volume `<COMPOSE_PROJECT_NAME>-postgres-data` (для проекта по умолчанию — `paperweave-postgres-data`). `make down` этот volume сохраняет. В MVP нет команды удаления данных. Для временного тестирования используется отдельный service `test-db` с `tmpfs`, без подключения пользовательского volume.

После изменения конфигурации выполните `make restart`. Если конфигурационный файл отсутствует или невалиден, launcher остановится до Compose-команд. Если миграция завершилась ошибкой, API и UI не запускаются.

Значение пароля в `config.example.toml` — только локальная заглушка. Не используйте примерный файл в доступной по сети среде и не помещайте пользовательский `config.toml` в Git.
