.PHONY: up down logs restart login sync backfill backup status

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

restart:
	docker compose restart bridge sync

login:
	docker compose run --rm -it bridge mifit login

sync:
	docker compose run --rm sync --days 7

backfill:
	docker compose run --rm sync --backfill

backup:
	./deploy/backup.sh

status:
	@curl -s -H "Authorization: Bearer $$BRIDGE_TOKEN" http://127.0.0.1:8787/v1/status | python3 -m json.tool || true
