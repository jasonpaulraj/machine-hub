# Development Setup Guide

## Problem: Docker Changes Not Reflecting

You're experiencing this issue because the current `docker-compose.yml` is designed for **production deployment**, not development. Here's what's happening:

### Root Causes:

1. **No Volume Mounts**: Your source code isn't mounted into the containers, so changes on your host machine don't affect the running containers.

2. **Production Builds**: The Dockerfiles create static builds:
   - **API**: Copies code at build time, runs with static files
   - **Web**: Builds a production bundle and serves it with nginx

3. **No Hot Reload**: Neither service is configured for development hot reload

## Solution: Development Environment

I've created a complete development setup that fixes these issues:

### New Files Created:

- `docker-compose.dev.yml` - Development compose file with volume mounts
- `machine-hub-api/Dockerfile.dev` - API development container with hot reload
- `machine-hub-web/Dockerfile.dev` - Web development container with Vite dev server
- `Makefile` - Development commands using make

### Key Features:

✅ **Volume Mounts**: Source code is mounted, changes reflect immediately
✅ **Hot Reload**: Both API (uvicorn) and Web (Vite) auto-reload on changes
✅ **Development Optimized**: Faster startup, better debugging
✅ **Isolated**: Separate containers/volumes from production

## Usage

### Quick Start:

```bash
# Start development environment
make dev-up

# Stop development environment
make dev-down

# View logs
make dev-logs

# Force rebuild (if you change dependencies)
make dev-rebuild

# Clean everything (nuclear option)
make dev-clean

# Show all available commands
make help
```

### Manual Commands:

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Stop development environment
docker-compose -f docker-compose.dev.yml down
```

### Development vs Production:

| Environment | Command | Purpose | Hot Reload |
|-------------|---------|---------|------------|
| **Development** | `make dev-up` | Code changes, debugging | ✅ Yes |
| **Production** | `make prod-up` | Deployment, testing | ❌ No |

## What Changed:

### API Development (`Dockerfile.dev`):
- Uses `uvicorn --reload` for hot reload
- Mounts source code as volume
- Installs `watchfiles` for better file watching

### Web Development (`Dockerfile.dev`):
- Runs `npm run dev` (Vite dev server)
- Mounts source code as volume
- Enables polling for file changes in Docker

### Volume Mounts:
```yaml
volumes:
  - ./machine-hub-api:/app          # API source code
  - ./machine-hub-web:/app          # Web source code
  - /app/node_modules               # Exclude node_modules
```

## Troubleshooting:

### Changes Still Not Reflecting?

1. **Check Volume Mounts**:
   ```bash
   docker-compose -f docker-compose.dev.yml ps
   ```

2. **Restart Services**:
   ```bash
   make dev-rebuild
   ```

3. **Check Logs**:
   ```bash
   make dev-logs
   ```

### Performance Issues?

- **File Watching**: Docker on macOS/Windows can be slow with file watching
- **Solution**: The dev setup includes polling fallbacks (`CHOKIDAR_USEPOLLING`, `WATCHFILES_FORCE_POLLING`)

### Port Conflicts?

- Development uses same ports as production by default
- Stop production containers first: `docker-compose down`
- Or modify ports in `docker-compose.dev.yml`

## Best Practices:

1. **Use Development Mode**: Always use `make dev-up` for development
2. **Production Testing**: Use `make prod-up` to test production builds
3. **Clean Regularly**: Run `make dev-clean` if you encounter issues
4. **Dependency Changes**: Run `make dev-rebuild` after changing package.json or requirements.txt

## Environment Variables:

The development setup uses the same environment variables as production:

```bash
# Copy and modify as needed
cp machine-hub-api/.env.example machine-hub-api/.env
```

Now your changes will reflect immediately without rebuilding! 🎉