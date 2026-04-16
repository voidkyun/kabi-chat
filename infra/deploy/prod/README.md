# Early Access Deploy

`infra/deploy/prod/` はアーリーアクセス向け単一 instance 構成の配備素材を置く場所です。

## 含まれるもの

- `docker-compose.yml`
  - reverse proxy, backend, PostgreSQL を同一 host 上で起動する
- `Caddy.Dockerfile`
  - Frontend の build と Caddy image の組み立てをまとめる
- `Caddyfile`
  - HTTPS 終端、SPA 配信、Backend API への reverse proxy
- `.env.example`
  - 本番で注入する secret と host 名の雛形
- `backup-postgres.sh`
  - 同一 host の PostgreSQL を SQL dump として退避する簡易スクリプト

## 前提

- Terraform で作成した Lightsail instance に Docker Engine / Docker Compose plugin を導入済みであること
- DNS が instance の static IP を向いていること
- `APP_DOMAIN` と Discord OAuth redirect の設定が一致していること

## 初回セットアップ

```bash
cp infra/deploy/prod/.env.example infra/deploy/prod/.env
docker compose -f infra/deploy/prod/docker-compose.yml --env-file infra/deploy/prod/.env build
docker compose -f infra/deploy/prod/docker-compose.yml --env-file infra/deploy/prod/.env up -d
```

`.env.example` で構文確認だけしたい場合は以下を使います。

```bash
DEPLOY_ENV_FILE=.env.example docker compose -f infra/deploy/prod/docker-compose.yml --env-file infra/deploy/prod/.env.example config
```

## 運用メモ

- DB は host 外に公開しません
- TLS 証明書は Caddy が自動更新します
- backup は `POSTGRES_USER` と `POSTGRES_DB` を export した上で `sh infra/deploy/prod/backup-postgres.sh` を実行します
- `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS`, `AUTH_FRONTEND_CALLBACK_URL`, `DISCORD_REDIRECT_URI` は同じ domain に揃えます
