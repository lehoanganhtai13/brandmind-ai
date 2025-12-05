# Valkey Docker Setup

Self-hosted Valkey (Redis fork) with Docker Compose, featuring environment variable-based password configuration.

## Quick Start

1. **Create environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and set your password:**
   ```bash
   VALKEY_USERNAME=brandmind
   VALKEY_PASSWORD=your_secure_password_here
   ```

3. **Start Valkey:**
   ```bash
   docker compose up -d
   ```

4. **Verify it's running:**
   ```bash
   docker compose logs -f valkey
   ```

## Configuration

### Environment Variables

- `VALKEY_USERNAME` - ACL username (default: `brandmind`)
- `VALKEY_PASSWORD` - ACL password (**required**, no default)

### Files

- `docker-compose.yml` - Docker Compose configuration
- `docker-entrypoint.sh` - Custom entrypoint that processes config template
- `conf/valkey.conf.template` - Configuration template with env var placeholders
- `.env` - Your environment variables (create from `.env.example`)

## How It Works

1. Docker Compose passes environment variables to the container
2. Custom entrypoint script (`docker-entrypoint.sh`) runs at startup
3. Script uses `envsubst` to replace `${VALKEY_USERNAME}` and `${VALKEY_PASSWORD}` in template
4. Generated config is saved to `/tmp/valkey.conf`
5. Valkey server starts with the generated configuration

## Usage

### Connect with valkey-cli

```bash
# From host
docker exec -it valkey-container valkey-cli

# Authenticate
AUTH brandmind your_password

# Test
PING
```

### Connect from Application

```python
import redis

client = redis.Redis(
    host='localhost',
    port=6379,
    username='brandmind',  # or use env var
    password='your_password',  # or use env var
    decode_responses=True
)

client.ping()
```

## Security Notes

⚠️ **Important:**
- Never commit `.env` file to git
- `.env` should be in `.gitignore`
- Use strong passwords in production
- Consider using Docker Secrets for production deployments

## Troubleshooting

### View generated config
```bash
docker exec valkey-container cat /tmp/valkey.conf
```

### Check environment variables
```bash
docker exec valkey-container env | grep VALKEY
```

### View entrypoint logs
```bash
docker compose logs valkey
```

## References

- [Valkey Documentation](https://valkey.io/topics/quickstart/)
- [Valkey ACL Guide](https://valkey.io/topics/acl/)
- [Docker Hub](https://hub.docker.com/r/valkey/valkey)
