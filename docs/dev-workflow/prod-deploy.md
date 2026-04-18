# Production Deploy Workflow

## Summary

`main` への merge 後、GitHub Actions の `Deploy Prod` workflow が prod host へ release bundle を転送し、`infra/deploy/prod/deploy.sh` を実行して本番更新します。deploy 対象は Frontend / Backend / `infra/deploy/prod/` の変更です。

本番 deploy は GitHub の `prod` environment を前提にし、credential は environment secrets / vars に寄せます。

## Deploy Flow

1. PR を `main` へ merge する
2. `Deploy Prod` が起動し、`infra/deploy/prod/docker-compose.yml` の `gateway` と `app` build を検証する
3. runner が `git archive` で release bundle を作成する
4. runner が `PROD_APP_ENV_FILE` を一時ファイルへ展開する
5. runner が SSH で prod host に release bundle と env file を転送する
6. prod host が `/opt/kabi-chat/releases/<git-sha>` に展開し、`/opt/kabi-chat/current` を差し替える
7. `infra/deploy/prod/deploy.sh` が `docker compose build app gateway` と `docker compose up -d --remove-orphans` を実行する

`workflow_dispatch` も有効にしているため、同じ revision を手動で再 deploy できます。

## GitHub Environment

GitHub 上で `prod` environment を作成し、以下を設定します。

### Secrets

- `PROD_APP_ENV_FILE`
  - `infra/deploy/prod/.env` の完成形をそのまま multi-line で保存する
- `PROD_SSH_PRIVATE_KEY`
  - prod host に入る deploy 用 private key
- `PROD_SSH_KNOWN_HOSTS`
  - `ssh-keyscan -H <prod-host>` の結果

### Variables

- `PROD_SSH_HOST`
  - prod host の FQDN または IP
- `PROD_SSH_USER`
  - prod host に SSH する user
- `PROD_DEPLOY_PATH`
  - release を配置する base path
  - 既定値は `/opt/kabi-chat`

必要であれば GitHub Environment Protection Rules で required reviewers を付け、`main` merge 後も deploy 実行前に人手承認を挟みます。

## Prod Host Preparation

Lightsail instance 側では以下を事前に満たします。

- Docker Engine と Docker Compose plugin を導入する
- deploy user を作成し、`docker` group に所属させる
- `mkdir -p /opt/kabi-chat/releases /opt/kabi-chat/shared` を実行できる権限を与える
- `PROD_SSH_PRIVATE_KEY` に対応する public key を `~/.ssh/authorized_keys` に登録する
- 初回だけ `PROD_SSH_KNOWN_HOSTS` 用に host key を採取する

GitHub-hosted runner から直接 SSH する場合、送信元 IP を固定 CIDR で絞りにくい点に注意します。SSH の source 制限を厳格に維持したい場合は、self-hosted runner か固定 IP を持つ runner を使います。GitHub の larger runners では static IP を割り当てられます。

## AWS Side Tasks

- `infra/terraform/environments/prod/terraform.tfvars` を用意し、Lightsail instance / static IP / firewall を apply する
- `APP_DOMAIN` の DNS を Lightsail static IP へ向ける
- 80 / 443 を公開し、22 は deploy 方法に応じて制限する
- 初回 deploy 前に Docker と Compose plugin を host に導入する
- snapshot と backup の運用時刻を決める

Terraform の `ssh_allowed_cidrs` を狭く保ちたい場合は、GitHub-hosted runner ではなく self-hosted runner への切り替えを検討します。

## Discord Developer Portal Tasks

- Production 用 redirect URI として `https://<APP_DOMAIN>/auth/discord/callback` を追加する
- Frontend callback と整合する `AUTH_FRONTEND_CALLBACK_URL=https://<APP_DOMAIN>/login/callback` を `PROD_APP_ENV_FILE` に入れる
- `APP_DOMAIN` を変更した場合は Discord 側 redirect URI も同時に更新する

Discord 側の redirect URI は Backend の `DISCORD_REDIRECT_URI` と完全一致させます。

## Updating Prod Env

`PROD_APP_ENV_FILE` には少なくとも `infra/deploy/prod/.env.example` の項目を埋めます。

- `APP_DOMAIN`
- `ACME_EMAIL`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `DISCORD_CLIENT_ID`
- `DISCORD_CLIENT_SECRET`
- `DISCORD_REDIRECT_URI`
- `JWT_SIGNING_KEY`
- `AUTH_FRONTEND_CALLBACK_URL`

`VITE_API_BASE_URL` は same-origin 配信を使う場合は空文字のままで構いません。

## Manual Recovery

GitHub Actions を使わず手動で復旧したい場合は、prod host 上で最新の source を配置してから以下を実行します。

```bash
sh infra/deploy/prod/deploy.sh
```
