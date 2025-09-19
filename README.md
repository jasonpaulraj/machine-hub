# Machine Hub

A comprehensive remote management system for machines with real-time monitoring, power control, and system metrics collection via Glances integration.

## 🚀 Features

### Core Functionality

- **Remote Power Control**: Wake-on-LAN, power on/off, restart machines
- **Real-time System Monitoring**: CPU, memory, disk, network metrics
- **Machine Management**: Add, configure, and organize multiple machines
- **Authentication**: JWT-based secure access control
- **Webhook Integration**: Receive system metrics from Glances
- **Home Assistant Integration**: Optional smart plug control for power management

### System Monitoring

- **CPU Metrics**: Usage percentage, user/system/iowait breakdown
- **Memory Monitoring**: RAM usage, swap utilization
- **Storage Tracking**: Disk usage and filesystem information
- **Network Statistics**: Interface monitoring and traffic data
- **Battery Status**: Power level and charging state (laptops)
- **System Information**: OS version, hostname, uptime tracking

### Power Management

- **Wake-on-LAN**: Network-based machine wake-up
- **Smart Plug Integration**: Physical power control via Home Assistant
- **Multiple Power States**: Support for sleep, hibernate, shutdown states
- **Scheduled Operations**: Automated power management tasks

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Web    │    │   FastAPI        │    │   MySQL         │
│   Frontend      │◄──►│   Backend        │◄──►│   Database      │
│   (Nginx)       │    │   (Python)       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         │              ┌────────▼────────┐
         │              │   Glances       │
         └──────────────►│   Webhook       │
                        │   Integration   │
                        └─────────────────┘
```

## 📋 Prerequisites

- Docker and Docker Compose
- Network access to target machines
- Glances installed on monitored machines
- (Optional) Home Assistant for smart plug integration

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd machine-hub

# Copy environment files
cp .env.example .env
cp machine-hub-api/.env.example machine-hub-api/.env
cp machine-hub-web/.env.example machine-hub-web/.env`
```

### 2. Build and Start

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up --build -d
```

### 3. Access the Application

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:3306

### Build Commands

```bash
# Build specific service
docker-compose build machine-hub-web
docker-compose build machine-hub-api

# Rebuild with no cache
docker-compose build --no-cache

# Rebuild and start all services
docker-compose build --no-cache && docker-compose up -d

# Build and start specific service
docker-compose up --build machine-hub-web
```

## 🌐 Nginx Proxy Configuration

The nginx configuration handles routing between frontend and backend:

### Key Features

- **API Proxying**: Routes `/api/*` requests to FastAPI backend
- **Webhook Handling**: Routes `/webhook/*` for Glances integration
- **SPA Support**: Fallback to `index.html` for React Router
- **Static Asset Optimization**: Caching and compression
- **Security Headers**: XSS protection and content type validation

## 📊 Glances Integration

### Installation on Target Machines

#### Windows Installation

```powershell
# Install via pip
pip install glances

# Or via chocolatey
choco install glances
```

#### Linux Installation

```bash
# Ubuntu/Debian
sudo apt install glances

# CentOS/RHEL
sudo yum install glances

# Via pip
pip install glances
```

### Starting Glances WITHOUT Auto-Discovery

#### Method 1: REST API Mode (Recommended)

```bash
# Start Glances REST API server
glances -w --disable-autodiscover

# With custom port
glances -w --port 61208 --disable-autodiscover

# With authentication
glances -w --disable-autodiscover --username admin --password secure123

# Bind to specific interface
glances -w --bind 0.0.0.0 --disable-autodiscover
```

#### Method 2: Webhook Mode (Direct Push)

```bash
# Configure Glances to send data directly
glances --export webhook --webhook-url http://your-server:3000/webhook/glances
```

#### Method 3: Configuration File

Create `~/.config/glances/glances.conf`:

```ini
[global]
# Disable auto-discovery
autodiscover=False

[webserver]
# REST API configuration
port=61208
bind=0.0.0.0

[webhook]
# Webhook export configuration
url=http://your-server:3000/webhook/glances
headers=X-Secret:optional_secret_for_webhook
```

Then start:

```bash
glances -w
```

### Testing Glances Integration

#### Test REST API Access

```bash
# Test local Glances API
curl http://localhost:61208/api/4/all

# Test remote machine
curl http://192.168.1.100:61208/api/4/all
```

#### Test Webhook Integration

```bash
# Use provided test script
python test_ip_access.py

# Send real Glances data
python send_real_glances_data.py
```

### Webhook Security

- **IP-based Access Control**: Only registered machine IPs can send data
- **Optional Secret Header**: `X-Secret` header validation
- **Data Validation**: Structured parsing and validation of metrics

## 🔌 Power Control Setup

### Wake-on-LAN Configuration

#### BIOS/UEFI Settings

1. Enable "Wake on LAN" or "Wake on PCIe"
2. Disable "ErP Ready" (Energy Related Products)
3. Enable "Wake on LAN from S5" (shutdown state)
4. Set "Deep Sleep Control" to "Disabled" or "S3 Only"

#### Windows Network Settings

1. Device Manager → Network Adapter → Properties
2. Power Management tab:
   - ✅ "Allow this device to wake the computer"
   - ✅ "Allow a magic packet to wake the computer"
3. Advanced tab:
   - Set "Wake on Magic Packet" to "Enabled"
   - Set "Wake on Pattern Match" to "Enabled"

#### Disable Windows Fast Startup

1. Control Panel → Power Options
2. "Choose what the power buttons do"
3. "Change settings that are currently unavailable"
4. ❌ Uncheck "Turn on fast startup (recommended)"

### Testing Wake-on-LAN

```bash
# Test with provided script
python test_wol.py

# Manual test with wakeonlan
wakeonlan AA:BB:CC:DD:EE:FF

# PowerShell test
Send-WOL -MacAddress "AA:BB:CC:DD:EE:FF" -IPAddress "192.168.1.255"
```

## 🏠 Home Assistant Integration (Optional)

### Setup Smart Plug Control

1. **Configure Home Assistant**:

   - Install and configure smart plugs
   - Create long-lived access token
   - Note entity IDs for each machine's plug

2. **Update Environment Variables**:

   ```bash
   HOME_ASSISTANT_URL=http://homeassistant.local:8123
   HOME_ASSISTANT_TOKEN=your_long_lived_token_here
   ```

3. **Configure Machine Entities**:
   - Add machines via web interface
   - Set Home Assistant entity ID for each machine
   - Test power control via dashboard

## 🛠️ Development

### Local Development Setup

```bash
# Backend development
cd machine-hub-api
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend development
cd machine-hub-web
npm install
npm run dev
```

### Database Migrations

```bash
# Run migrations
docker-compose exec machine-hub-api python -m app.init_db

# Manual SQL migrations
docker-compose exec db mysql -u control -p control < migrations/002_move_system_info_to_machines.sql
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Test authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

## 📝 API Endpoints

### Authentication

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user

### Machine Management

- `GET /api/machines` - List all machines
- `POST /api/machines` - Add new machine
- `GET /api/machines/{id}` - Get machine details
- `PUT /api/machines/{id}` - Update machine
- `DELETE /api/machines/{id}` - Delete machine

### Power Control

- `POST /api/machines/{id}/power` - Control machine power
  - Actions: `on`, `off`, `restart`, `wake`

### System Monitoring

- `GET /api/machines/{id}/snapshots` - Get system metrics
- `GET /api/machines/{id}/snapshots/latest` - Latest metrics

### Webhooks

- `POST /webhook/glances` - Receive Glances data
- `GET /webhook/glances/test` - Test webhook endpoint
- `POST /webhook/cleanup-snapshots` - Clean old data

## 🔍 Troubleshooting

### Common Issues

#### Wake-on-LAN Not Working

1. Check BIOS settings (disable ErP Ready)
2. Verify network adapter settings
3. Disable Windows Fast Startup
4. Test from sleep mode first
5. Check network cable connection

#### Glances Connection Issues

1. Verify Glances is running: `glances -w --disable-autodiscover`
2. Check firewall settings (port 61208)
3. Test API access: `curl http://machine-ip:61208/api/4/all`
4. Verify IP registration in machines table

#### Docker Build Failures

1. Clear Docker cache: `docker system prune -a`
2. Rebuild without cache: `docker-compose build --no-cache`
3. Check disk space and memory
4. Verify network connectivity for package downloads

### Logs and Debugging

```bash
# View service logs
docker-compose logs machine-hub-api
docker-compose logs machine-hub-web
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f machine-hub-api

# Debug specific container
docker-compose exec machine-hub-api bash
docker-compose exec machine-hub-web sh
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
