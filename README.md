# Raspberry Pi Assistant

A Telegram bot assistant designed to run on a Raspberry Pi. Delivers news digests, research paper summaries, email management, and system monitoring — with minimal AI dependency.

---

## Features

| Command | Description |
|---------|-------------|
| `/papers [topic]` | 5 newest arXiv papers for a topic, or all saved topics |
| `/settopics t1, t2` | Set your research topic list |
| `/topics` | Show current research topics |
| `/news [category]` | Latest headlines (world, tech, science, us, business) |
| `/inbox` | Check unread emails |
| `/send <to> <subject> <body>` | Send an email |
| `/sysinfo` | CPU, RAM, disk, temperature |
| `/digest` | Trigger the daily digest manually |
| `/pause [reason]` | Pause the bot |
| `/resume` | Resume the bot |
| `/status` | Show pause state + system info |
| `/help` | List all commands |

### Daily Digest (8:00 AM)
Every morning the bot sends:
- Top headlines across world, tech, and science
- 5 newest arXiv papers for each of your saved topics
- Current system status

### Auto-Pause
The bot monitors system health every 2 minutes. If any threshold is exceeded it pauses itself, alerts you, and resumes automatically when metrics return to normal.

| Metric | Threshold |
|--------|-----------|
| CPU | 85% |
| RAM | 90% |
| Temperature | 75°C |

---

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/yourname/Raspberry-Pi-Assistant.git
cd Raspberry-Pi-Assistant
pip install -r requirements.txt
```

### 2. Create a Telegram bot

1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the token you receive

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
TELEGRAM_TOKEN=your_telegram_bot_token

# Optional — email features
EMAIL_ADDRESS=you@gmail.com
EMAIL_PASSWORD=your_app_password

# Optional — LLM features (future)
OPENAI_API_KEY=your_openai_key
```

**Gmail App Password:** Your regular Gmail password won't work. You need to generate an App Password:
1. Google Account → Security → 2-Step Verification must be on
2. Search for "App Passwords" and generate one for this app
3. Note: school/Workspace accounts may have this disabled by the admin

### 4. Set your research topics

Once the bot is running, send:
```
/settopics algebraic topology, number theory, machine learning
```

### 5. Run

```bash
python -m assistant.main
```

To run persistently on the Pi (survives reboots):
```bash
# Create a systemd service
sudo nano /etc/systemd/system/pi-assistant.service
```

```ini
[Unit]
Description=Raspberry Pi Assistant
After=network.target

[Service]
ExecStart=/usr/bin/python3 -m assistant.main
WorkingDirectory=/home/pi/Raspberry-Pi-Assistant
Restart=on-failure
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable pi-assistant
sudo systemctl start pi-assistant
```

---

## Project Structure

```
assistant/
├── main.py                  # Entry point
├── router.py                # Plain-text message fallback
├── interfaces/
│   └── telegram_bot.py      # Command handlers, bot setup
├── modules/
│   ├── research.py          # arXiv search, topic management
│   ├── news.py              # RSS feed headlines
│   ├── email.py             # Gmail send / inbox
│   ├── sysinfo.py           # System metrics + thresholds
│   └── scheduler.py         # Daily digest + system monitor
├── utils/
│   ├── config.py            # Environment variable loading
│   ├── state.py             # Pause flag, registered chat IDs
│   ├── logger.py            # Logging setup
│   └── openai_client.py     # LLM client (optional)
└── data/
    ├── topics.json          # Saved research topics
    └── chat_ids.json        # Registered Telegram chat IDs
```

---

## Notes

- Email features require a Gmail account with IMAP enabled and an App Password
- LLM summarisation for research papers is implemented but disabled by default (`use_llm=False`). Set `OPENAI_API_KEY` and pass `use_llm=True` to enable
- Temperature monitoring reads `/sys/class/thermal/thermal_zone0/temp` (Raspberry Pi) with a psutil fallback for other platforms
