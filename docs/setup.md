# 部署手册

目标机器：Ubuntu 24.04 + Docker + Nginx（宝塔面板也可）。

## 1. 上传代码

```bash
mkdir -p /opt/health-bridge
# 从本机（或 git clone）把仓库内容放到 /opt/health-bridge
cd /opt/health-bridge
```

## 2. 配置环境

```bash
cp .env.example .env
chmod 600 .env
TOKEN=$(openssl rand -hex 32)
sed -i "s/^BRIDGE_TOKEN=.*/BRIDGE_TOKEN=${TOKEN}/" .env
# 编辑 .env：
#   MCP_ALLOWED_HOSTS=你的域名,你的域名:443
echo "$TOKEN"   # 记下来，Muse 连接器要用
```

## 3. 启动

```bash
docker compose up -d --build
docker compose ps
```

## 4. 登录小米账号（二维码）

```bash
docker compose run --rm -it bridge mifit login
```

终端里会出现二维码；用手机「小米运动健康」扫码并在手机上确认。
如果小米要求二次安全确认，按提示打开链接确认后重跑一次。

## 5. 同步

```bash
docker compose run --rm sync --days 7      # 最近 7 天
docker compose run --rm sync --backfill    # 回填 BACKFILL_DAYS 天（默认 365）
```

`sync` 容器之后每天 04:30（`TZ` 时区）自动做 7 天增量。

## 6. 反向代理 + TLS

把 `deploy/nginx/health.example.com.conf` 中的 `HEALTH_HOST` 替换成你的域名，放到
`/www/server/panel/vhost/nginx/<域名>.conf`（宝塔）或 `/etc/nginx/conf.d/`，然后用
面板/`certbot` 申请证书，`nginx -t && nginx -s reload`。

如果面板不代管证书，用 webroot 方式：

```bash
mkdir -p /www/wwwroot/<域名>
# 先放上面 conf 的 80 端口 server 块（含 acme-challenge），reload
docker run --rm -v /www/wwwroot/<域名>:/var/www \
  -v /etc/letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly --webroot -w /var/www -d <域名> \
  --email you@example.com --agree-tos --non-interactive
# 再把 443 server 块的证书路径改成 /etc/letsencrypt/live/<域名>/...
```

## 7. 验证

```bash
TOKEN=$(grep ^BRIDGE_TOKEN .env | cut -d= -f2)
curl -s -H "Authorization: Bearer $TOKEN" https://<域名>/v1/status | python3 -m json.tool
curl -s -H "Authorization: Bearer $TOKEN" "https://<域名>/v1/summary?days=7" | head -c 800
curl -s -H "Authorization: Bearer $TOKEN" "https://<域名>/v1/summary?days=7&format=md"
```

MCP 冒烟（本机）：

```bash
uv run python - <<'PY'
import asyncio
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

async def main():
    async with streamablehttp_client(
        "http://127.0.0.1:8788/mcp",
        headers={"Authorization": "Bearer <TOKEN>"},
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([t.name for t in tools.tools])
            result = await session.call_tool("get_daily_summary", {"days": 7})
            print(result.content[0].text[:500])

asyncio.run(main())
PY
```

## 8. 备份

```bash
./deploy/backup.sh
crontab -e   # 5 5 * * * /opt/health-bridge/deploy/backup.sh
```

备份含 `mifit_session`（等于小米账号凭据），建议在 `.env` 设置 `BACKUP_PASSPHRASE` 加密。
