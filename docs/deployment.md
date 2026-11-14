# 部署记录（health.xp6.top）

## 主机

- 服务器：`38.76.201.208`（Ubuntu 24.04，Docker 29 + Compose v5，宝塔 Nginx）
- 代码目录：`/opt/health-bridge`
- 容器：`xiaomi-health-bridge`（REST 8787 + MCP 8788，仅绑 127.0.0.1）、`xiaomi-health-sync`
- 卷：`health_data`（SQLite）、`mifit_session`（小米登录态）
- 公网入口：`https://health.xp6.top`（Nginx vhost：`/www/server/panel/vhost/nginx/health.xp6.top.conf`）
- 证书：`/etc/letsencrypt/live/health.xp6.top`，续期 cron `/etc/cron.d/health-bridge-tls`

## 路由

| 路径 | 后端 |
| --- | --- |
| `/admin` | 管理后台（ADMIN_PASSWORD 登录） |
| `/v1/*`、`/openapi.json`、`/docs` | REST（Bearer） |
| `/mcp` | MCP streamable HTTP（Bearer） |

## 运维

```bash
cd /opt/health-bridge
docker compose ps
docker compose logs -f --tail=100 bridge
docker compose logs -f --tail=100 sync
docker compose run --rm -it bridge mifit login   # 扫码登录（也可用 /admin）
docker compose run --rm sync --days 7            # 手动同步
./deploy/backup.sh                               # 备份
./deploy/restore.sh <stamp>                      # 恢复
```

## 密钥

- `BRIDGE_TOKEN` / `ADMIN_PASSWORD` 在 `/opt/health-bridge/.env`（0600）
- 小米登录态在 `mifit_session` 卷，备份时会被打包（建议设置 `BACKUP_PASSPHRASE`）
- 不要把 `.env`、`backups/`、登录态提交到 git
