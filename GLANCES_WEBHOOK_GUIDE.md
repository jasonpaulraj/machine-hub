# Glances Webhook Data Sender Guide

This guide explains how to set up and run the `send_real_glances_data.py` script to send system metrics to a webhook endpoint across different operating systems.

## Prerequisites

### All Operating Systems
- Python 3.6 or higher
- `requests` library: `pip install requests`
- Network access to your webhook endpoint

### macOS Specific
- `powermetrics` command (built-in on macOS)
- Administrator/sudo access for temperature readings
- System password for enhanced sensor data

### Linux Specific
- `sensors` command: `sudo apt-get install lm-sensors` (Ubuntu/Debian) or `sudo yum install lm_sensors` (RHEL/CentOS)
- Optional: `nvidia-smi` for NVIDIA GPU monitoring

### Windows Specific
- PowerShell execution policy set to allow scripts
- Optional: Hardware monitoring tools for enhanced metrics

## Installation

1. **Download the script:**
   ```bash
   # Clone the repository or download send_real_glances_data.py
   wget https://your-repo/send_real_glances_data.py
   # or
   curl -O https://your-repo/send_real_glances_data.py
   ```

2. **Install Python dependencies:**
   ```bash
   pip install requests
   # or
   pip3 install requests
   ```

3. **Make script executable (Linux/macOS):**
   ```bash
   chmod +x send_real_glances_data.py
   ```

## Configuration

### Environment Variables (Optional)
You can set these environment variables instead of using command-line arguments:

```bash
# Linux/macOS
export WEBHOOK_URL="http://your-server:8009/webhook/glances"
export API_SECRET="your-api-secret"
export ENV="production"
export SYSTEM_PASSWORD="your-sudo-password"  # macOS only

# Windows (PowerShell)
$env:WEBHOOK_URL="http://your-server:8009/webhook/glances"
$env:API_SECRET="your-api-secret"
$env:ENV="production"
$env:SYSTEM_PASSWORD="your-admin-password"

# Windows (Command Prompt)
set WEBHOOK_URL=http://your-server:8009/webhook/glances
set API_SECRET=your-api-secret
set ENV=production
set SYSTEM_PASSWORD=your-admin-password
```

## Usage

### Basic Usage

**Linux/macOS:**
```bash
python3 send_real_glances_data.py --webhook-url http://192.168.100.72:8009/webhook/glances --api-secret test-secret --environment production --interval 60
```

**Windows:**
```cmd
python send_real_glances_data.py --webhook-url http://192.168.100.72:8009/webhook/glances --api-secret test-secret --environment production --interval 60
```

### Enhanced macOS Usage (with temperature sensors)
```bash
python3 send_real_glances_data.py --webhook-url http://192.168.100.72:8009/webhook/glances --api-secret test-secret --environment production --interval 60 --system-password your-password
```

### Command Line Arguments

| Argument | Short | Description | Required | Default |
|----------|-------|-------------|----------|---------|
| `--webhook-url` | `-u` | Webhook endpoint URL | Yes* | From env var |
| `--api-secret` | `-s` | API secret key | Yes* | From env var |
| `--environment` | `-e` | Environment (development/production) | No | development |
| `--interval` | `-i` | Interval between sends (seconds) | No | 5 |
| `--system-password` | | System password for sudo (macOS) | No | None |
| `--env` | | Environment check (production hides debug) | No | From ENV var |

*Required unless set via environment variables

### Debug vs Production Mode

**Development Mode (shows debug output):**
```bash
python3 send_real_glances_data.py --environment development --webhook-url http://localhost:8009/webhook/glances --api-secret test-secret
```

**Production Mode (minimal output):**
```bash
python3 send_real_glances_data.py --environment production --webhook-url http://your-server:8009/webhook/glances --api-secret your-secret
# or
python3 send_real_glances_data.py --env production --webhook-url http://your-server:8009/webhook/glances --api-secret your-secret
```

## Running as a Service

### Linux (systemd)

1. Create service file `/etc/systemd/system/glances-webhook.service`:
```ini
[Unit]
Description=Glances Webhook Data Sender
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/script
Environment=WEBHOOK_URL=http://your-server:8009/webhook/glances
Environment=API_SECRET=your-api-secret
Environment=ENV=production
ExecStart=/usr/bin/python3 /path/to/send_real_glances_data.py --interval 60
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

2. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable glances-webhook.service
sudo systemctl start glances-webhook.service
```

### macOS (launchd)

1. Create plist file `~/Library/LaunchAgents/com.glances.webhook.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.glances.webhook</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/send_real_glances_data.py</string>
        <string>--webhook-url</string>
        <string>http://your-server:8009/webhook/glances</string>
        <string>--api-secret</string>
        <string>your-api-secret</string>
        <string>--environment</string>
        <string>production</string>
        <string>--interval</string>
        <string>60</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

2. Load and start:
```bash
launchctl load ~/Library/LaunchAgents/com.glances.webhook.plist
launchctl start com.glances.webhook
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "At startup")
4. Set action: Start a program
   - Program: `python`
   - Arguments: `C:\path\to\send_real_glances_data.py --webhook-url http://your-server:8009/webhook/glances --api-secret your-secret --environment production --interval 60`
   - Start in: `C:\path\to\script\directory`

## Troubleshooting

### Common Issues

1. **Permission denied (macOS):**
   ```bash
   # Run with sudo for temperature readings
   sudo python3 send_real_glances_data.py --system-password your-password ...
   ```

2. **Module not found:**
   ```bash
   pip install requests
   # or
   pip3 install requests
   ```

3. **Connection refused:**
   - Check webhook URL is correct
   - Verify network connectivity
   - Ensure webhook server is running

4. **Authentication failed:**
   - Verify API secret is correct
   - Check webhook server logs

### Monitoring

**Check service status (Linux):**
```bash
sudo systemctl status glances-webhook.service
sudo journalctl -u glances-webhook.service -f
```

**Check service status (macOS):**
```bash
launchctl list | grep glances
log show --predicate 'process == "python3"' --last 1h
```

**Check task status (Windows):**
- Open Task Scheduler
- Check "Task Scheduler Library"
- View task history

## Example Output

The script sends JSON data with system metrics including:
- CPU usage and temperature
- Memory usage
- Disk usage
- Network statistics
- GPU metrics (if available)
- Client IP information

```json
{
  "cpu": {"percent": 25.5},
  "memory": {"percent": 60.2},
  "sensors": [
    {"label": "CPU Temperature", "value": 45.0, "unit": "°C"}
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```