# TikTok Monitor Discord Bot

A production-ready Discord bot that monitors TikTok accounts and sends notifications when new videos are posted. Includes a web dashboard with Discord OAuth2 login.

## Features

- Slash commands for managing TikTok account subscriptions
- Automatic background monitoring (configurable interval)
- Duplicate video prevention
- Rich Discord embed notifications with **"Watch on TikTok"** button
- Multi-server support
- Web dashboard to manage settings, view logs, and force scans
- Runs entirely on Termux (Android) or any Linux server

---

## Installation on Termux

### 1. Update packages

```bash
pkg update && pkg upgrade -y
```

### 2. Install Python and Git

```bash
pkg install python git -y
```

### 3. Clone the repository

```bash
git clone https://github.com/CreeperRick/TikTok-Ping-Bot
cd TikTok-Ping-Bot
```

### 4. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate
```

### 5. Install dependencies

```bash
pkg update -y
pkg install clang python libffi libffi-dev openssl openssl-dev rust binutils -y
pip install --only-binary :all: pydantic pydantic-core
pip install -r requirements.txt
```

### 6. Configure environment variables

Copy the example environment file:

```bash
cp .env.example .env
nano .env
```

Fill in your Discord and application credentials.

### 7. Make the start script executable

```bash
chmod +x main.py
```

### 8. Run the bot

```bash
./main.py
```

The web dashboard will be available at:

```text
http://0.0.0.0:8000
```

Use your Termux device's local IP address to access it from other devices on the same network.

---

## Commands

| Command | Description |
|----------|-------------|
| `/addtiktok <username>` | Subscribe to a TikTok account (Admin only) |
| `/removetiktok <username>` | Remove a TikTok subscription (Admin only) |
| `/listtiktok` | List subscribed TikTok accounts for this server |
| `/setchannel #channel` | Set the notification channel (Admin only) |
| `/forcecheck` | Manually trigger a scan for new videos |
| `/status` | Show bot status and statistics |
| `/help` | Display help information |

---

## Environment Variables

| Variable | Description |
|-----------|-------------|
| `DISCORD_TOKEN` | Discord bot token |
| `DISCORD_CLIENT_ID` | Discord OAuth2 Client ID |
| `DISCORD_CLIENT_SECRET` | Discord OAuth2 Client Secret |
| `DISCORD_REDIRECT_URI` | OAuth2 redirect URI (e.g. `http://localhost:8000/auth/callback`) |
| `SECRET_KEY` | Session encryption key |
| `TIKTOK_POLL_INTERVAL_MINUTES` | Interval between TikTok scans |
| `DATABASE_URL` | SQLite database path |

---

## Docker (Optional)

### Build and run with Docker

```bash
docker build -t tiktok-bot .
docker run -d \
  --name tiktok-bot \
  -p 8000:8000 \
  --env-file .env \
  tiktok-bot
```

### Using Docker Compose

```bash
docker-compose up -d
```

---

## License

Specify your project license here (MIT, Apache 2.0, GPL, etc.).

---

## Support

If you encounter issues, check the logs through the web dashboard or open an issue in the repository.
