# 运维手册

## 常用命令

```bash
docker compose ps
docker compose logs -f --tail=200 bridge
docker compose logs -f --tail=200 sync
docker compose run --rm sync --days 7      # 手动同步
docker compose run --rm -it bridge mifit login   # 重新扫码登录
./deploy/backup.sh
./deploy/restore.sh <stamp>
```

## 管理密码

- 首次登录用 `.env` 的 `ADMIN_PASSWORD`。
- 登录后在「设置 → 修改管理密码」修改（只存 PBKDF2 哈希到 SQLite）；修改后其他浏览器会话失效。
- 忘记密码：`docker compose run --rm bridge python -m health_bridge.admin --reset-password`，之后用 `.env` 的密码登录。

## 同步节奏

- 默认每天 04:30（`Asia/Shanghai`）增量同步，回看 7 天。
- 「同步」页可改为固定间隔（5–1440 分钟），并调整每次回看 3/7/14/30 天；保存后 30 秒内生效，无需重启。
- 启动容器时也会同步一次；首次无数据会回填 `BACKFILL_DAYS` 天。
- 小米云端本身有上传延迟，频繁抓取不会让数据更实时，反而增加风控风险。

## 健康检查

```bash
curl -s http://127.0.0.1:8787/healthz
TOKEN=$(grep ^BRIDGE_TOKEN .env | cut -d= -f2)
curl -s -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8787/v1/status
```

关注：

- `session_expired`: true → 需要重新扫码。
- `last_sync_at`: 超过 2 天没更新 → 看 sync 日志。
- `domains.*.last_error`: 某个域持续失败（小米接口变动/限流）。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| 401 | Token 不对；或 MCP 的 Host 不在 `MCP_ALLOWED_HOSTS` |
| 503 auth_expired | 重新 `mifit login` |
| 429 | 客户端请求太快；调大 `RATE_LIMIT_PER_MIN` 或降低调用频率 |
| 数据缺当天 | 小米云延迟；等下一次同步，或 `sync --days 2` |
| 某域报 API error | 小米接口变更；升级 `mifit`（`docker compose build --pull`） |
| Muse 连不上 | 域名/证书/防火墙；`curl https://<域名>/healthz` |

## 安全

- `.env` 与 `backups/` 权限 600；`mifit_session` 卷等同小米账号凭据。
- 泄露 Token 后：改 `.env` 的 `BRIDGE_TOKEN`，`docker compose up -d`，在 Muse 里更新凭据。
- 服务器密码已更换，SSH 仅密钥登录。

## 升级

```bash
git pull
docker compose up -d --build
```

升级后跑一次 `docker compose run --rm sync --days 7`，再看 `/v1/status`。

## 恢复演练

1. `./deploy/backup.sh`
2. 记下最新 stamp。
3. `./deploy/restore.sh <stamp>`
4. `curl /v1/status`，确认行数与最后同步时间。
