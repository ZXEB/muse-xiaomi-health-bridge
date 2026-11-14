# Xiaomi Health Bridge for Meta Muse

只读桥接：把小米运动健康（Mi Fitness）云端数据同步到自己的服务器，并以 **远程 MCP + REST(OpenAPI)** 的形式提供给 Meta Muse 的自定义连接器使用。

- 数据来源：`mifit`（非官方，读取你自己的小米账号云端已同步数据）
- 服务端：Docker Compose（`bridge` + `sync`），SQLite 本地库
- 对外：`https://<域名>/mcp`（Streamable HTTP MCP，Bearer 鉴权）+ `/v1/*`（REST/OpenAPI）
- 只读：不写账号、不控制手表；默认不含 GPS 轨迹

## 架构

```text
小米手环/手表 → 小米运动健康 App → 小米云
                                      │ mifit（二维码登录，session 在卷里）
                                      ▼
                     ┌──────── docker compose ────────┐
                     │ sync：04:30 增量 + 首次回填     │
                     │        ↓ 写                     │
                     │ health_data 卷（SQLite WAL）    │
                     │        ↑ 读                     │
                     │ bridge：REST 8787 + MCP 8788    │
                     └─────────────────────────────────┘
                                      │ Nginx / TLS + Bearer
                                      ▼
                                 Meta Muse（Custom Connector → Skill）
```

## 快速开始（服务器）

```bash
cd /opt/health-bridge
cp deploy/health-bridge.env.example .env
# 编辑 .env：BRIDGE_TOKEN=$(openssl rand -hex 32)、TZ=Asia/Shanghai
docker compose up -d --build

# 首次登录：终端显示二维码，用手机「小米运动健康」扫码
docker compose run --rm -it bridge mifit login

# 先同步 7 天，再回填（默认 365 天，可改 BACKFILL_DAYS）
docker compose run --rm sync --days 7
docker compose run --rm sync --backfill
```

验证：

```bash
curl -s -H "Authorization: Bearer $BRIDGE_TOKEN" https://health.example.com/v1/summary?days=7
curl -s -H "Authorization: Bearer $BRIDGE_TOKEN" https://health.example.com/v1/status
```

## 接入 Meta Muse

在 Muse 里发一条消息（Token 用 Muse 的安全凭据流程输入，不要贴在聊天里）：

```text
Build a custom integration to my self-hosted health-data service.
Remote MCP server over streamable HTTP: https://<域名>/mcp
Auth: Authorization: Bearer <token> (I will enter it through the secure credential flow).
Tools: health_status, get_daily_summary, get_daily_metrics, get_sleep, get_steps,
get_heart_rate_daily, get_spo2_daily, get_stress_daily, get_weight, get_calories,
get_workouts, sync_now.
Connect with the official MCP SDK, call get_daily_summary for the last 7 days end to end,
show me the results, set the connector to read-only, and save the integration as a reusable skill.
```

也可以把 `https://<域名>/openapi.json` 交给 Muse 自动生成连接器。

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/healthz` | 公开 |
| GET | `/openapi.json`、`/docs` | 公开 |
| GET | `/v1/status` | 同步状态、登录状态、行数 |
| GET | `/v1/summary?days=7&format=md\|json` | 摘要 |
| GET | `/v1/metrics?from=&to=&fields=` | 日指标 |
| GET | `/v1/sleep|steps|heart-rate|spo2|stress|weight|activity|calories` | 单域 |
| GET | `/v1/workouts` | 运动记录 |
| POST | `/v1/sync?days=7` | 手动同步 |
| POST | `/mcp` | MCP（Streamable HTTP） |

鉴权：`Authorization: Bearer <BRIDGE_TOKEN>` 或 `X-API-Key`。日期为 `Asia/Shanghai` 本地日，区间包含首尾，单次 ≤92 天。

## 备份与恢复

```bash
./deploy/backup.sh          # SQLite + mifit 登录卷 → ./backups/
./deploy/restore.sh <stamp> # 停止 → 还原 → 启动
```

备份含 mifit 登录态（等于小米账号级凭据），请设置 `BACKUP_PASSPHRASE` 加密并妥善保管。

## 安全

- 小米 session/passToken 只存在服务器卷 `mifit_session`，不要外传。
- `BRIDGE_TOKEN` 只放 `.env`（0600），90 天轮换。
- 服务只监听 `127.0.0.1`，由宿主机 Nginx 终止 TLS。
- Muse 侧把连接器设为只读；工具返回的数据会进入 Meta 模型侧，只暴露摘要。

## 开发

```bash
uv sync
uv run pytest
```

## 免责声明

非官方项目，与小米无关。仅用于读取你自己的数据；自动访问可能违反小米服务条款，存在账号被限流/限制的风险，使用风险自负。输出的任何内容都不构成医疗建议。
