# Hori

Hori is a production-grade, modular Telegram group moderation bot built with
Python 3.11+, Pyrogram v2, and MongoDB. It is inspired by bots like Miss Rose,
providing warnings, welcomes, keyword filters, content locks, antispam, member
approvals, admin connections, and cross-chat federations.

## Features

- **Moderation** — mute, unmute, kick, ban, unban, pin, unpin, purge
- **Warnings** — configurable warn limits with automatic mute/kick/ban actions
- **Welcomes** — customizable welcome and goodbye messages with placeholders
- **Filters** — keyword-triggered auto-replies per chat
- **Locks** — restrict text, media, stickers, URLs, forwards, and more
- **Antispam** — automatic flood detection and muting
- **Reports** — let members flag messages to admins with `/report`
- **Approvals** — exempt trusted users from locks and antispam
- **Connections** — manage a group's settings remotely from a private chat
- **Federations** — share a ban list (`/fban`) across multiple chats
- Async MongoDB persistence via Motor, with a clean repository layer
- Structured logging (console + rotating file handlers)
- Background job scheduling via APScheduler
- Fully typed, documented, and organized for long-term maintainability

## Project Structure

```
Hori/
├── bot/            # Pyrogram client factory and application lifecycle
├── config/         # Environment-driven configuration
├── core/           # Logging, scheduler, decorators, exceptions, startup
├── database/       # Mongo connection, models, and repositories
├── handlers/       # /start and /help
├── modules/        # Feature modules (moderation, warns, welcomes, ...)
├── filters/        # Custom Pyrogram filters (admin, owner, chat type)
├── keyboards/       # Inline and reply keyboard builders
├── utils/          # Shared helper functions
├── logs/           # Rotating log files (created at runtime)
├── tests/          # Test suite
└── main.py         # Entry point
```

## Installation

### Prerequisites

- Python 3.11 or newer
- A MongoDB instance (local, Atlas, or Railway plugin)
- A Telegram API ID/hash from [my.telegram.org](https://my.telegram.org)
- A bot token from [@BotFather](https://t.me/BotFather)

### Steps

```bash
git clone https://github.com/your-username/hori.git
cd hori
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and fill in your credentials.

## Environment Variables

| Variable         | Required | Description                                             |
|-------------------|----------|-----------------------------------------------------------|
| `API_ID`          | Yes      | Telegram API ID from my.telegram.org                     |
| `API_HASH`        | Yes      | Telegram API hash from my.telegram.org                   |
| `BOT_TOKEN`       | Yes      | Bot token from @BotFather                                 |
| `MONGO_URI`       | Yes      | MongoDB connection URI                                    |
| `MONGO_DB_NAME`   | No       | Database name (default: `hori_bot`)                       |
| `OWNER_ID`        | Yes      | Telegram user ID of the bot owner                          |
| `SUDO_USERS`      | No       | Comma-separated Telegram user IDs with sudo privileges     |
| `LOG_CHANNEL_ID`  | No       | Channel ID for bot event logging                           |
| `ENVIRONMENT`     | No       | `development` or `production` (default: `production`)      |
| `LOG_LEVEL`       | No       | Logging level (default: `INFO`)                            |
| `SESSION_NAME`    | No       | Pyrogram session name (default: `hori_bot`)                 |
| `WORKERS`         | No       | Pyrogram worker thread count (default: `8`)                 |
| `PARSE_MODE`      | No       | Default message parse mode (default: `HTML`)                |

## Running Locally

```bash
python main.py
```

The bot will connect to MongoDB, ensure indexes exist, start its scheduler,
log in to Telegram, register all handlers, and idle until stopped with
`Ctrl+C`.

## Deploying to Railway

1. Push this repository to GitHub.
2. Create a new Railway project and select **Deploy from GitHub repo**.
3. Add a MongoDB plugin (or use an external MongoDB Atlas cluster) and copy
   its connection string into `MONGO_URI`.
4. Set the remaining environment variables from the table above in the
   Railway project's **Variables** tab.
5. Railway will detect `railway.json` and run `python main.py` automatically
   on every deploy.

## Contributing

Contributions are welcome. Please:

1. Fork the repository and create a feature branch.
2. Follow the existing code style: full type hints, docstrings on every
   class and function, and PEP8-compliant formatting.
3. Keep new features modular — add new feature modules under `modules/`
   with a `register(client)` entry point.
4. Open a pull request describing your change.

## License

Released under the [MIT License](LICENSE).
