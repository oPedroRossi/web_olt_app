# Web OLT App

Simple telecom web tool for Huawei OLT operations.

## What it does

- Search ONUs by customer description (`display ont info by-desc`)
- Show ONU status, serial, RX optical power, and offline alarm hint
- Trigger ONU HTTP unlock (`ont wan-access http <fsp ont_id> enable`)
- Trigger ONU reboot (`ont force-reset <fsp ont_id>`)

## Stack

- Python 3.10+
- Flask
- Netmiko

## Project structure

- `app.py`: app entrypoint
- `backend/config/settings.py`: environment loading and app settings
- `backend/routes/olt_routes.py`: route registration
- `backend/controllers/olt_controller.py`: request/response orchestration
- `backend/services/olt_service.py`: Huawei OLT business/service logic
- `backend/utils/validators.py`: payload and input validation helpers
- `templates/index.html`: web UI
- `static/script.js`: frontend API calls and behavior
- `static/style.css`: styles
- `olt.wsgi`: WSGI entrypoint
- `.env.example`: environment template
- `requirements.txt`: runtime dependencies

## Quick start

1. Create virtual env and install dependencies.

```bash
python -m venv venv
# Linux/macOS
source venv/bin/activate
# Windows PowerShell
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Configure environment.

```bash
cp .env.example .env
```

Replace all placeholder values in `.env`.

3. Run locally.

```bash
python app.py
```

Open `http://localhost:5169`.

## Environment variables

- `APP_HOST`: Flask bind host
- `APP_PORT`: Flask bind port
- `FLASK_DEBUG`: `false` in production
- `LOG_LEVEL`: `INFO`, `WARNING`, `ERROR`
- `OLT_USERNAME`: SSH username for OLT
- `OLT_PASSWORD`: SSH password for OLT
- `OLT_PORT`: SSH port (default `22`)
- `NETMIKO_SESSION_LOG`: optional command/session log file
- `OLT_OPTIONS`: JSON array shown in UI and used as OLT allow-list

Example `OLT_OPTIONS` value (placeholder only):

```json
[
  { "name": "OLT_A", "ip": "<OLT_IP_1>" },
  { "name": "OLT_B", "ip": "<OLT_IP_2>" }
]
```

## Security notes

- Keep `.env` out of git.
- Use dedicated low-privilege OLT account.
- Keep `FLASK_DEBUG=false`.
- Restrict app access to trusted operator network.
- Rotate OLT credentials periodically.

## Troubleshooting

- `OLT credentials not configured.`
: set `OLT_USERNAME` and `OLT_PASSWORD` in `.env`.
- `OLT not allowed.`
: OLT IP not listed in `OLT_OPTIONS`.
- Empty ONU result
: customer description may not match OLT records.
