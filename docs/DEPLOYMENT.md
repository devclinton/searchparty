# Deployment Guide

## Self-Hosted Deployment

### Requirements
- Docker and Docker Compose
- Domain name with SSL certificate
- 2GB+ RAM, 2+ CPU cores

### Quick Start

```bash
# Clone the repository
git clone https://github.com/devclinton/searchparty.git
cd searchparty

# Copy environment template
cp .env.example .env
# Edit .env with your settings (database, secret key, domain)

# Start all services
docker compose -f docker-compose.prod.yml up -d

# Run migrations
docker compose exec backend python -m app.db.migrate

# Access the app at https://your-domain.com
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SP_DATABASE_URL` | PostgreSQL connection string | Yes |
| `SP_SECRET_KEY` | JWT signing key (generate with `openssl rand -hex 32`) | Yes |
| `SP_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL (default: 30) | No |
| `SP_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL (default: 7) | No |

### Reverse Proxy (Nginx)

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}
```

### Database Backup

```bash
# Backup
pg_dump -U searchparty searchparty > backup_$(date +%Y%m%d).sql

# Restore
psql -U searchparty searchparty < backup_20260414.sql
```

### Monitoring
- Health check: `GET /health`
- Application logs: `docker compose logs -f backend`
- Database metrics: Monitor via `pg_stat_activity`
