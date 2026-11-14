# 在 Meta Muse 里接入

## 一句话提示词

把下面内容发到 Muse（把 `<域名>` 换掉；Token 不要在聊天里贴，等它要凭据时走安全输入框）：

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

Muse 问 transport 时回答 **HTTP（streamable）**，问鉴权时回答 **Bearer token**。

## 备选：OpenAPI

Muse 也可以从 OpenAPI 生成连接器：给它
`https://<域名>/openapi.json`，鉴权同上。REST 与 MCP 读取同一份 SQLite，结果一致。

## 验收提问

- 我昨晚睡了多久？深睡多少？
- 上周静息心率有什么变化？
- 我最近一次运动是什么？跑了多远？
- 这周步数日均多少？

## 权限

- Settings → Connectors 里把该连接器设为 **read-only**（本服务本身也只读）。
- 工具结果会进入 Meta 的模型侧；服务端只返回摘要与必要字段，默认不含 GPS。

## 排错

- 401：Token 不对，重发；或检查 `MCP_ALLOWED_HOSTS` 是否含域名。
- 503 `auth_expired`：服务器上重新 `docker compose run --rm -it bridge mifit login`。
- 没数据：先 `docker compose run --rm sync --days 7`，再看 `/v1/status`。
