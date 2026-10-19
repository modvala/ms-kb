# MCP-версия kb: сначала локальный сервер для Claude Desktop, удалённый доступ к vault пока не нужен

Дата: 2026-10-19. Основа: код v0.5.0 и документы v2.1 этого репозитория (часть документов ещё не закоммичена), спецификация MCP 2026-07-28, документация Python SDK, справка Anthropic и OpenAI, документация Tailscale, Cloudflare и ngrok. Все внешние источники открыты 2026-10-19. Продуктовые факты про планы и клиенты меняются быстро, поэтому у каждого стоит дата проверки. Пометка **[не проверено]** значит, что первоисточник недоступен, молчит или противоречит другим. Хранилище пользователя не открывалось, команды `kb`, которые пишут, не запускались.

## Краткий вывод

- **Сервер написать легко, труднее до него дотянуться.** Официальный Python SDK (пакет `mcp` 2.3.0 от 2026-10-02, класс `MCPServer`) по умолчанию работает через stdio. Подкоманда `kb mcp` займёт несколько десятков строк поверх `write.py` ([PyPI](https://pypi.org/project/mcp/), [SDK: Running](https://py.sdk.modelcontextprotocol.io/run/)). Главный вопрос в другом: какой чат-клиент вообще может достучаться до процесса на Mac.
- **Сервер на Mac видит только Claude Desktop.** Desktop запускает локальные stdio-серверы, а с `.mcpb` и `server.type: "uv"` ставит их в один клик. claude.ai, мобильные приложения Claude и ChatGPT подключают только удалённые серверы, причём ходят к ним из облака провайдера, так что localhost им недоступен ([Claude: custom connectors](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp), [OpenAI: custom MCP server](https://developers.openai.com/api/docs/guides/custom-mcp-server)).
- **Большую часть сценария можно закрыть, не выставляя vault в интернет.** Разговоры claude.ai живут в аккаунте. Исследование, начатое в вебе или на телефоне, открывается в Claude Desktop на Mac и сохраняется через локальный сервер. Документация этого прямо не обещает, нужна ручная проверка **[не проверено]**.
- **Удалённый доступ к vault на Mac означает публичную точку записи в личную базу.** Для этого нужны туннель (Tailscale Funnel, Cloudflare Tunnel или ngrok), собственный OAuth и Mac, который не спит. Кроме того, текст из чата, который мог написать кто угодно, получает путь к записи. Туннели Anthropic доступны только на Enterprise. Если удалённый вариант когда-нибудь понадобится, безопаснее сервер вне Mac, который только пишет во «входящие» на отдельной ветке remote.
- **Архитектура ms-kb подходит для MCP лучше, чем кажется.** Защиты уже в коде, а не в тексте skill (`docs/personal-knowledge-design-v2.md:332`). Diff gate из этапа 5 (`--dry-run` → хеш → `--approve`) напрямую ложится на пару инструментов «предпросмотр / применить». Хосты к тому же сами просят подтверждения на запись. Мешают две вещи: `cli._finish` печатает в stdout, что stdio запрещает, а сценарий `add-knowledge` в чат-клиент через MCP сегодня не доставить, потому что расширение Skills over MCP Claude не поддерживает, а ChatGPT поддерживает частично.
- **Документы v2 сейчас прямо исключают MCP и ChatGPT.** Это записано в `docs/personal-knowledge-design-v2.md:46-48`, `:317`, `:567-569`, `docs/personal-knowledge-roadmap-v2.md:151` («an MCP wrapper; ChatGPT» во frozen) и `docs/personal-knowledge-user-stories-v2.md:50`. Чтобы начать работу, нужно решение и правка документов до v2.2.
- **ChatGPT в MVP не годится.** Документация OpenAI противоречива в том, можно ли на личных планах подключать свой MCP-сервер с записью. Справочный центр не открылся для проверки.
- **Рекомендация.** Сейчас нужна дешёвая передача без MCP: summary из чата сохраняется файлом, а `add-knowledge` в Claude Code работает по этому файлу. Это абзац в skill на шаге 5c. Локальный `kb mcp` для Claude Desktop стоит делать после этапа 5, отдельным шагом этапа 6 или первым пунктом «Later». Удалённый сервер и ChatGPT пусть остаются frozen.

## 1. Что умеют клиенты

### MCP в двух абзацах

Текущая ревизия спецификации — **2026-07-28**. Сервер предлагает *tools* (их вызывает модель), *resources* (данные) и *prompts* (шаблоны, которые вызывает пользователь). Стандартных транспортов два: **stdio**, где клиент запускает сервер подпроцессом, и **Streamable HTTP**, где каждое сообщение отправляется отдельным POST на один endpoint. В этой ревизии из протокола убраны сессии и GET-поток, запросы стали самодостаточными ([спецификация](https://modelcontextprotocol.io/specification/latest), [транспорты](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports), [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)). На stdio сервер **MUST NOT** писать в stdout ничего, кроме MCP-сообщений, а логи идут в stderr ([stdio](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio)). Авторизация в целом необязательна. Если HTTP-сервер её делает, он следует OAuth 2.1, обязан публиковать Protected Resource Metadata (RFC 9728), а регистрация клиента предпочтительно идёт через Client ID Metadata Documents. Для stdio учётные данные берутся из окружения ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). Локальный HTTP-сервер **MUST** проверять `Origin` против DNS rebinding и **SHOULD** слушать только 127.0.0.1.

У инструмента есть аннотации `readOnlyHint`, `destructiveHint`, `idempotentHint` и `openWorldHint`. Клиент **MUST** считать их недоверенными, если сервер не доверенный. Спецификация рекомендует держать человека в цикле с правом отклонить вызов ([tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)). Ответ `server/discover` может содержать поле `instructions`, то есть подсказку модели, как пользоваться сервером ([discover](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)). Каждый запрос несёт в `_meta` поле `io.modelcontextprotocol/clientInfo` с именем и версией клиента. Отдельное расширение **Skills over MCP** (`io.modelcontextprotocol/skills`, SEP-2640 стал Final 2026-09-13) отдаёт папки со `SKILL.md` через resources ([обзор](https://modelcontextprotocol.io/extensions/skills/overview), [WG](https://modelcontextprotocol.io/community/working-groups/skills-over-mcp)). В Python SDK v2 сервер создаётся через `MCPServer("...")` и `@mcp.tool(annotations=ToolAnnotations(...))`, а запускается вызовом `mcp.run()` (stdio) или `mcp.run(transport="streamable-http")`, по умолчанию на 127.0.0.1:8000/mcp ([tools](https://py.sdk.modelcontextprotocol.io/servers/tools/), [run](https://py.sdk.modelcontextprotocol.io/run/)). SDK требует Python ≥ 3.10, а ms-kb требует ≥ 3.11, так что конфликта нет.

### Клиенты (проверено 2026-10-19)

| Клиент | Локальный stdio | Удалённый HTTP | Планы | Мобильные | Запись |
|---|---|---|---|---|---|
| **Claude Desktop** (macOS, Windows) | **Да**: `claude_desktop_config.json` или расширение `.mcpb` (zip с `manifest.json`, `server.type` может быть `node`, `python`, `binary` или `uv`; с `uv` зависимости ставит хост) ([MCPB](https://claude.com/docs/connectors/building/mcpb.md), [manifest](https://github.com/modelcontextprotocol/mcpb/blob/main/MANIFEST.md)) | Коннекторы аккаунта, через облако Anthropic | Локальные расширения работают «в desktop-приложении при входе в claude.ai», ограничения по планам для Free/Pro/Max не названы ([add-unlisted](https://claude.com/docs/connectors/custom/add-unlisted)) | — | Да, через запросы подтверждения инструментов |
| **claude.ai (веб)** | Нет: локальные серверы «separate mechanism», в claude.ai и Cowork недоступны | **Да**, custom connector по URL. OAuth или «No sign-in»; заголовки с ключом в бете для ограниченного круга организаций | Free (1 коннектор), Pro, Max, Team, Enterprise; на Team/Enterprise добавляет только Owner ([custom connectors](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp), [add-unlisted](https://claude.com/docs/connectors/custom/add-unlisted)) | — | Да. В режиме Research инструменты вызываются «without further approval» |
| **Claude iOS/Android** | Нет | Коннекторы из аккаунта: облачное подключение действует «across every Claude client, including … the mobile apps»; настройка описана только для веба | Как у claude.ai | **Да** | Как у claude.ai |
| **ChatGPT (веб)** | Нет | **Да**: Plugins → Add custom MCP server; SSE и streaming HTTP; OAuth или без аутентификации ([custom MCP](https://developers.openai.com/api/docs/guides/custom-mcp-server), [connect](https://developers.openai.com/plugins/deploy/connect-chatgpt)) | **[не проверено, источники противоречат]**: гайд разработчика называет только «workspace» и «account policies», [help.openai.com](https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt) вернул 403, сторонний обзор от 2026-09-21 пишет, что custom-коннекторы перешли на workspace-планы ([Peliqan](https://peliqan.io/blog/chatgpt-mcp/)) | Не документировано | Подтверждение записи по умолчанию; инструмент без `readOnlyHint` считается записью |
| **ChatGPT + Secure MCP Tunnel** | `tunnel-client` на своей машине long-poll'ом достаёт запросы и передаёт их локальному stdio- или HTTP-серверу, без входящих портов ([guide](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels.md)) | — | Нужны организация Platform и API-ключ; доступность для личных Plus/Pro **[не проверено]** | — | — |
| **ChatGPT desktop (Codex)** | Codex поддерживает stdio и HTTP; «The ChatGPT desktop app, Codex CLI, and IDE extension share this configuration» (`~/.codex/config.toml`) ([Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)) | Да | — | — | Видят ли эти серверы обычные чаты, а не только Codex-треды, **[не проверено]**. Skills ms-kb там уже работают (`docs/clients-v0.md:53-55`) |
| **Claude Code** | Да (stdio, HTTP, ws) | Да; коннекторы claude.ai подтягиваются автоматически при входе подпиской ([Claude Code MCP](https://code.claude.com/docs/en/mcp)) | — | — | Уже есть shell и skills, MCP ничего не добавляет |
| **Codex CLI/IDE, Cursor** | Да ([Codex](https://learn.chatgpt.com/docs/extend/mcp?surface=cli); Cursor есть в [матрице клиентов MCP](https://modelcontextprotocol.io/extensions/client-matrix)) | Да | — | — | То же: shell и skills уже есть |

Из таблицы следуют три вывода.

1. **На Mac stdio-сервер подхватывает только Claude Desktop.** Остальные чат-клиенты увидят только сервер с публичным HTTPS-адресом.
2. **Коннектор, добавленный на claude.ai, работает и в мобильном приложении, и в Claude Code.** Последнее надо учитывать: удалённый `kb`-коннектор появится в Claude Code рядом с skills. Это вторая дорога записи, её стоит отключить через `ENABLE_CLAUDEAI_MCP_SERVERS=false` или `disableClaudeAiConnectors` ([Claude Code MCP](https://code.claude.com/docs/en/mcp)).
3. **Расширение Skills over MCP у Claude не отмечено вовсе, у ChatGPT — «Partial»** ([матрица](https://modelcontextprotocol.io/extensions/client-matrix)). Положить `add-knowledge` на сервер и рассчитывать, что Claude его подхватит, пока нельзя.

### Об «артефакте из Claude Code»

- **В Claude Code** уже есть shell и `add-knowledge`, так что сохранять можно прямо там. Артефакт там — опубликованная на claude.ai HTML-страница или файл. MCP для этого случая не нужен.
- **В claude.ai** у артефакта есть кнопки копирования и скачивания ([Claude Help](https://support.claude.com/en/articles/9487310)). Модель держит текст артефакта в контексте и может передать его аргументом в инструмент записи. Но страница темы v2 — это синтез, а не копия (`docs/personal-knowledge-design-v2.md:661`). Поэтому артефакт служит сырьём для черновика страницы, а не телом файла.

## 2. Как дотянуться до локального vault

| Вариант | Что нужно | Mac должен работать | Что открыто наружу | Соответствие архитектуре |
|---|---|---|---|---|
| **A. Claude Desktop + stdio** | `kb mcp` в конфиге Desktop или `.mcpb` | Да, разговор открывается на Mac | Ничего; содержимое инструментов уходит модели Anthropic, как и в Claude Code | Полное: тот же `kb`, тот же lock, та же история |
| **B. Туннель к Mac** | HTTP-режим `kb mcp` под LaunchAgent, туннель, свой OAuth | Да, круглосуточно | Публичный URL, через который пишут в vault | Код тот же, но появляется сетевая поверхность и аутентификация |
| **C. Туннель провайдера** | Anthropic MCP tunnels или OpenAI Secure MCP Tunnel | Да | Исходящее соединение к провайдеру | Как B, но без публичного URL |
| **D. Сервер вне Mac → Git remote** | Небольшой сервер на хостинге с токеном на запись в репозиторий; на Mac новая команда приёма | Нет | Хостинг держит токен записи в vault-репо | Нужны новая команда и новые правила; `kb sync` сейчас не умеет pull |
| **E. Удалённый read-only (search/fetch)** | Как B или D, только чтение | Как B или D | Чтение всей личной базы из облачного чата | Меньше риск записи, больше риск утечки |

**B: туннели.**

| Туннель | Условия | Ограничения |
|---|---|---|
| [Tailscale Funnel](https://tailscale.com/kb/1223/funnel) | Доступен на всех планах, в бете; только домен `*.ts.net` и порты 443, 8443, 10000 | Трафик публичный, аутентификации посетителей у Funnel нет; есть «non-configurable bandwidth limits»; на macOS нужен open-source вариант приложения |
| Cloudflare Tunnel | Соединение исходящее; для публикации приложения нужно «add a website to Cloudflare», то есть свой домен ([create tunnel](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/)) | Quick Tunnels предназначены для тестов: случайное имя, не больше 200 запросов одновременно, «do not support Server-Sent Events» ([quick tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)). Сервер тогда должен отвечать JSON, а не SSE |
| [ngrok free](https://ngrok.com/docs/pricing-limits/free-plan-limits/) | Один dev-домен `*.ngrok-free.app` | 20 000 HTTP-запросов и 1 ГБ в месяц; промежуточная страница не мешает API-клиентам |

Ни один туннель не решает аутентификацию. claude.ai принимает OAuth (по CIMD, DCR или своему клиенту) либо «No sign-in», а заголовки с ключом доступны в бете ограниченному кругу ([add-unlisted](https://claude.com/docs/connectors/custom/add-unlisted)). Значит, придётся поднимать или арендовать authorization server, а MCP-сервер должен проверять audience токена ([authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). Вариант «без входа, зато с секретным URL» — это по сути bearer-токен в адресе, для записи в личную базу он не подходит.

**C: туннели провайдеров.**

- [Anthropic MCP tunnels](https://claude.com/docs/connectors/mcp-tunnels/overview) доступны в research preview только организациям на Enterprise. Они требуют Docker или Kubernetes и по умолчанию ходят только в частные диапазоны RFC 1918, поэтому пользователю не подходят.
- OpenAI Secure MCP Tunnel умеет работать с локальным stdio-сервером. Это единственный путь из ChatGPT без публичного адреса, но доступность для личного аккаунта **[не проверено]**.

**D: сервер вне Mac.** Небольшой удалённый MCP-сервер, например на бесплатном хостинге, мог бы класть Markdown в remote, а не в vault. Ограничения такие:

- Писать в основную ветку нельзя. `kb sync` никогда не делает pull, а после чужого коммита push отвергается как non-fast-forward (`src/ms_kb/history.py:279-288`, `src/ms_kb/cli.py:377-420`). Значит, нужна отдельная ветка или отдельный репозиторий «входящих» и новая команда на Mac, которая их забирает.
- Ни валидации, ни `secretscan`, ни провенанса из `_finish` на хостинге не будет, если не переносить туда пакет целиком.
- Готовый [GitHub MCP server](https://github.com/github/github-mcp-server) (remote, OAuth или PAT) даёт такую запись без кода. Но тогда агент пишет мимо `kb`, а это прямо противоречит правилу «only through kb» (`docs/personal-knowledge-design-v2.md:330`). Допустимо это только для отдельного репозитория-буфера, не для vault.
- «Входящие» как очередь спорят с решениями v2 «без статусов» и «без move/delete» (`docs/personal-knowledge-design-v2.md:155`, `:420`). Параллельный отчёт `reports/Источники на потом: захват и summary.md` (вариант D, inbox) приходит к тому же выводу.

**Итог.** Вариант A покрывает основной сценарий «исследовал в чате, сохранил» ценой одного условия: сохранять, сидя за Mac. Варианты B–E оправданы, только если нужно сохранять с телефона, когда Mac недоступен. Такой потребности в документах нет: мобильный доступ — пункт «Later» про синхронизацию (`docs/personal-knowledge-roadmap-v2.md:146`, US-20 target в `docs/personal-knowledge-user-stories-v2.md:359`).

## 3. Как ложится на архитектуру ms-kb

### Точка входа и упаковка

- **Подкоманда.** `kb mcp [--transport stdio|http]` добавляется в `build_parser` (`src/ms_kb/cli.py:779`). Зависимость `mcp` тянет HTTP-стек, поэтому её стоит сделать опциональным extra (`ms-kb[mcp]`), а без extra `kb mcp` должна печатать подсказку установки. Сейчас зависимостей всего две (`pyproject.toml`: `ruamel.yaml`, `tomli-w`).
- **Запуск из Claude Desktop.** Desktop — GUI-приложение без PATH из shell, поэтому в конфиге нужен абсолютный путь `~/.local/bin/kb`. С той же проблемой PATH skills уже сталкиваются (`src/ms_kb/skills/add-knowledge/SKILL.md:29`). Позже можно собрать `.mcpb` с `server.type: "uv"`, чтобы Desktop сам ставил зависимости.
- **Установка.** `kb install-skills` или `kb setup` могли бы предлагать дописать блок в `claude_desktop_config.json`, но только с согласия пользователя: `kb setup` не меняет настройки молча (`docs/personal-knowledge-design-v2.md:607`).

### Что надо переделать

- `write.py` уже чистый: `new_note` и `extend_note` возвращают `Result` и ничего не печатают (`src/ms_kb/write.py:66-131`, `:148-209`), а `save` отказывает при одновременном изменении (`src/ms_kb/write.py:212-226`).
- А вот `_finish` (`src/ms_kb/cli.py:591-615`) печатает результат, `_check_secrets` бросает `WriteError` (`src/ms_kb/cli.py:547-557`), а `main` превращает ошибки в stderr (`src/ms_kb/cli.py:896-909`). Для MCP нужен слой (условно `ms_kb/api.py`), который выполняет шаги `_finish` — lock, коммит внешних правок, `save`, `commit_write`, manifest — и **возвращает** структуру с путём, действием, предупреждениями и коммитом. CLI и MCP вызывают его одинаково.
- Любой `print` в этом пути на stdio-транспорте ломает протокол (см. правило stdio выше).
- `vaultstate.lock` — межпроцессный `fcntl.flock` (`src/ms_kb/vaultstate.py:51`), так что долго живущий сервер и CLI не конфликтуют, пока сервер не кэширует состояние vault между вызовами.

### Инструменты и команды

| MCP-инструмент | Команда `kb` | Аннотации |
|---|---|---|
| `kb_status` | `kb where` (версии, предупреждение о рассинхроне) | readOnly |
| `kb_search` | `kb search --json` (`src/ms_kb/cli.py:520`, `src/ms_kb/search.py:105`) | readOnly |
| `kb_index` | `kb index --json` (v0.6) | readOnly |
| `kb_read` | чтение файла с проверкой, что путь внутри vault (`resolve_in_vault`, `src/ms_kb/write.py:134`); в чате нет файловых инструментов, поэтому нужен отдельный инструмент или resource `kb://…` | readOnly |
| `kb_new_preview` / `kb_new` | `kb new topic --dry-run` / `kb new topic`; дубликаты отвергает `find_duplicates` (`src/ms_kb/search.py:153-186`) | read / write |
| `kb_rewrite_preview` / `kb_rewrite` | `kb rewrite --dry-run` → отчёт и хеш / `--approve HASH` (`docs/personal-knowledge-design-v2.md:449-477`) | read / write, `destructiveHint: true` |
| `kb_link`, `kb_extend` | `kb link`, `kb extend` (только добавление строк) | write, не destructive |
| `kb_my_words` | `kb my-words` | write; стоит отложить, текст пользователя дословно лучше писать из CLI |

**Не выставлять:** `sync`, `restore`, `init`, `setup`, `update`, `doctor --ack`, а также флаги `--allow-secret-like`, `--allow-shrink` и `--force`. Это команды и флаги пользователя (`docs/personal-knowledge-design-v2.md:447`, `src/ms_kb/skills/add-knowledge/SKILL.md:21`). `allow_similar` можно оставить параметром `kb_new`, но в описании требовать, чтобы сначала был отказ и явное «да» пользователя.

### Чем заменить skill в чат-клиенте

Skills — «часть продукта» и предполагают shell: «they need only a shell and `kb`» (`docs/personal-knowledge-design-v2.md:337`). В чат-клиенте их пути таковы:

1. **Инвариант в коде.** Дубликаты, diff gate, защищённый раздел, секреты и скрытый текст уже не зависят от клиента (`docs/personal-knowledge-design-v2.md:332`). Это главное, что MCP получает бесплатно.
2. **Описания инструментов.** Модель видит их всегда. Туда идут короткие правила: писать только по просьбе, сначала `kb_index` и `kb_search`, одна страница за запуск, сначала preview и показ diff пользователю, флаги пользователя не передавать.
3. **`instructions` в `server/discover`.** Поле есть в спецификации, но учитывают ли его claude.ai и ChatGPT, **[не проверено]**.
4. **MCP prompts `add-knowledge` и `kb-recall`.** Это шаблоны, которые вызывает пользователь. Их тело можно генерировать из `SKILL.md`, заменив shell-команды именами инструментов. Как их показывают Claude Desktop и claude.ai, **[не проверено]**.
5. **Custom skill в claude.ai.** В Customize > Skills можно загрузить ZIP. Функция есть на Free, Pro, Max, Team и Enterprise, но требует включённого code execution ([Claude Help](https://support.claude.com/en/articles/12512180-using-skills-in-claude)). Чат-вариант `add-knowledge`, который вызывает инструменты коннектора, — самый полный перенос сценария. Совместную работу skill с MCP-коннектором надо проверить руками **[не проверено]**.
6. **Skills over MCP.** Это правильный механизм на будущее, но сегодня Claude его не поддерживает (см. матрицу).

### Провенанс

Сейчас `agent` определяется только по `CLAUDECODE=1` (`src/ms_kb/provenance.py:14-17`, `:30-35`), а трейлеры собираются в `trailers()` (`src/ms_kb/provenance.py:57-66`). У MCP-сервера переменных окружения клиента нет, но каждый запрос несёт `clientInfo` (name, version). Предлагается:

- писать трейлеры `Kb-Agent: <clientInfo.name>` и `Kb-Transport: mcp-stdio|mcp-http`, причём `Kb-Agent` считать самоназванием клиента: спецификация прямо говорит, что `serverInfo` self-reported, и для `clientInfo` логика та же;
- в `Kb-Skill` писать `add-knowledge`, если запись шла через prompt или skill, и не выдумывать его в остальных случаях (US-12: «Unknown values … are not invented», `docs/personal-knowledge-user-stories-v2.md:268`);
- версию правил брать из версии пакета сервера, потому что `installed.toml` для чат-клиента не применим (`src/ms_kb/installer.py:167`).

### Что поменять в документах

| Документ | Что сказано сейчас | Что поменять |
|---|---|---|
| `docs/personal-knowledge-design-v2.md:46-48` | MCP в «not planned» | Убрать MCP из этого списка |
| `docs/personal-knowledge-design-v2.md:317` | «MCP, subagents and hooks are not used» | Заменить решением про локальный MCP |
| `docs/personal-knowledge-design-v2.md:337` | Skills «need only a shell and `kb`» | Добавить чат-вариант без shell |
| `docs/personal-knowledge-design-v2.md:567-569` | §12.2 «ChatGPT out of scope» | Добавить подраздел про чат-клиенты |
| `docs/personal-knowledge-roadmap-v2.md:151` | «an MCP wrapper» во frozen | Перенести в «Later» или в этап 6 |
| `docs/personal-knowledge-user-stories-v2.md:50` | Список AI-клиентов | Добавить Claude Desktop |
| `docs/personal-knowledge-user-stories-v2.md:287-296` (US-15) | «All clients write through the same CLI» | Формулировка остаётся верной, если MCP вызывает тот же код |
| `docs/clients-v0.md` | — | Ручная проверка Desktop |

## 4. Безопасность

- **«Летальная триада».** Сюда входят доступ к приватным данным, недоверенный контент и возможность что-то отправить наружу ([Willison](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)). Чат с веб-поиском и инструментами `kb_search`/`kb_read` собирает все три сразу: страница, найденная при исследовании, может велеть модели найти в базе что-то и вставить в URL запроса. Отсюда правило: **читающие инструменты только в локальном варианте A**, где пользователь видит каждый вызов. Удалённый вариант, если он появится, должен быть «только запись во входящие» без чтения.
- **Запись по внушению.** Граница доверия v2 — это отсутствие delete/move, хеш одобрения, защита от сжатия, защищённый `## In my words`, Git-история и remote вне досягаемости агента (`docs/personal-knowledge-design-v2.md:594-600`). Через MCP она сохраняется целиком, потому что код один. Но хеш доказывает только, что записано то же, что показал preview, а не что пользователь это видел: модель может вызвать preview и apply подряд. Так же обстоит дело и в CLI, где агент запускает обе команды. Реальная преграда — подтверждение в хосте:
  - ChatGPT подтверждает запись по умолчанию ([custom MCP](https://developers.openai.com/api/docs/guides/custom-mcp-server));
  - Claude спрашивает разрешение, но «Always allow» и режим Research его отключают ([custom connectors](https://support.claude.com/en/articles/11175166-getting-started-with-custom-connectors-using-remote-mcp)).

  Поэтому в документации нужно писать прямо: не нажимать «Always allow» для пишущих `kb_*` и не включать коннектор в Research. Механизм elicitation позволил бы серверу самому спросить пользователя, но поддержка в Claude и ChatGPT **[не проверено]**.
- **Сетевая поверхность.** Удалённый вариант добавляет публичный URL, OAuth-сервер, проверку audience токена, `Origin` и rate limit (спецификация: «Servers MUST … rate limit tool invocations»), а ещё Mac, который нельзя усыплять. Funnel и Quick Tunnels сами доступ не ограничивают.
- **Куда уходят данные.** Даже локальный stdio-сервер отдаёт результаты инструментов облачной модели. Это та же модель приватности, что у Claude Code, читающего vault, но её стоит назвать явно. Удалённый вариант добавляет ещё и туннельного провайдера.
- **Секреты.** Проверка на ключеподобные строки срабатывает при любой записи (`src/ms_kb/cli.py:547-557`), так что секрет, вставленный в чат, в vault не попадёт.
- **Песочница.** MCP-сервер работает с правами пользователя вне песочницы агента, как и `kb` сейчас (`docs/personal-knowledge-design-v2.md:607`). Новой дыры это не создаёт, при условии что сервер не выставляет ничего, кроме `kb`-операций.

## 5. Альтернативы без MCP

| Вариант | Цена | Правила skill | С телефона | Риск |
|---|---|---|---|---|
| **A1. Передача через файл в Claude Code.** В чате просим summary как Markdown-артефакт, скачиваем или копируем, затем в Claude Code «`/add-knowledge` по файлу ~/Downloads/x.md» | Абзац в `add-knowledge`: разрешить материал из файла, который назвал пользователь, как часть разговора. Файл остаётся вне vault, это не «raw-source folder» (`docs/personal-knowledge-design-v2.md:661`) | Все: поиск темы, takeaways, diff | Нет (нужен Mac) | Нет новых |
| **A2. Тот же чат в Claude Desktop + локальный `kb mcp`** | Слой `api.py`, около 8 инструментов, prompts, тесты | Почти все, через описания и prompts | Начать можно, сохранить нельзя | Низкий |
| **B. `kb import <file>`** без модели | Небольшая | Нет: без модели нет синтеза темы, а запись мимо diff gate противоречит US-24 | Нет | Создаёт заметки не того типа |
| **C. Вручную в Obsidian** | Ноль | Нет: ни валидации, ни провенанса; `kb sync` закоммитит правку как внешнюю (`src/ms_kb/history.py:149`) | Только с будущей синхронизацией (`docs/personal-knowledge-roadmap-v2.md:146`) | Нет |
| **D. ChatGPT** | Как A1: копировать или экспортировать, затем Claude Code. Либо desktop-приложение в режиме Codex, где skills уже работают | Все | Нет | Нет |

`kb import` как отдельная команда не нужна. A1 делает то же самое и при этом не обходит этап 5. A1 стоит сделать первым в любом случае: он проверит, насколько часто сценарий возникает на самом деле, прежде чем вкладываться в MCP.

## 6. Рекомендация

1. **Сейчас, в рамках этапа 5c.** Добавить в `add-knowledge` 0.6.0 источник «файл, названный пользователем» (A1). Это одно правило в skill и одна строка в README, без изменений кода.
2. **После этапа 5, отдельным шагом этапа 6 или первым пунктом «Later».** Делать локальный MCP после этапа 5, а не раньше, потому что этап 5 меняет саму модель записи (`rewrite`, хеш одобрения, `link`, `my-words`), и обёртка над v0.5 устарела бы через месяц. Состав MVP:
   - `ms_kb/api.py` вынимает из `_finish` логику без печати, CLI переходит на него;
   - `kb mcp` (stdio) в extra `ms-kb[mcp]`, сервер на `MCPServer`, инструменты из таблицы §3 с аннотациями, prompts `add-knowledge` и `kb-recall`, сгенерированные из `SKILL.md`, и `instructions`;
   - провенанс по `clientInfo` (`Kb-Agent`, `Kb-Transport`);
   - тесты через клиент SDK в памяти и CI-smoke `kb mcp` (вызвать `kb_search` и получить отказ `kb_new` на дубликате);
   - документация: блок для `claude_desktop_config.json`, предупреждение про «Always allow» и Research, design v2.2.

   **Готово, когда:** разговор, начатый на claude.ai или на телефоне и открытый в Claude Desktop на Mac, сохраняется ровно одной страницей темы после показанного diff; дубликат отвергается; коммит несёт `Kb-Agent` клиента; `kb doctor` остаётся чистым.
3. **Оставить frozen:** удалённый HTTP-сервер, туннели и ChatGPT. Вернуться к ним, если появится реальная потребность сохранять с телефона без Mac. Порядок тогда такой: сначала проверить, может ли синхронизация vault на телефон (пункт «Later») закрыть эту потребность. Если нет — делать сервер «только запись во входящие» вне Mac на отдельной ветке, без читающих инструментов, с OAuth через внешний IdP. ChatGPT подключать только после того, как подтвердится, что личный план разрешает custom MCP с записью.

## 7. Открытые вопросы для пользователя

1. Где именно проходят исследования: в вебе claude.ai, в мобильном приложении, в Claude Desktop или в ChatGPT? Какой у вас план ChatGPT?
2. Устраивает ли «сохраняю, когда сижу за Mac»? Если да, удалённый вариант не нужен.
3. Как часто это бывает? Если раз в неделю, хватит ли A1 (файл → `add-knowledge` в Claude Code)?
4. Допустимо ли, чтобы чат-клиент *читал* базу (`kb_search` и `kb_read`), или из чата нужна только запись?
5. Готовы ли вы держать отдельный чат-вариант `add-knowledge`, загруженный в claude.ai (Customize > Skills), рядом с основным?
6. Записывать ли в коммит имя клиента (`claude-desktop`, `chatgpt`) по самоназванию клиента, понимая, что его никто не проверяет?
7. «Артефакт из Claude Code» означает работу в самом Claude Code, где `add-knowledge` уже доступен? Или имеется в виду артефакт claude.ai, который надо перенести?
