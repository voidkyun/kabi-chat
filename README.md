# kabi-chat

markdown, tex をサポートする軽量なチャットツールです。Frontend / Backend / Infrastructure / docs をモノレポで管理します。

## Repository Layout

```text
.
├── frontend/              # React SPA (npm)
├── backend/               # Django / DRF API (Poetry)
├── infra/
│   └── terraform/         # AWS IaC (Terraform)
├── docs/                  # アーキテクチャと運用ルールの正本
├── docker-compose.yml     # ローカル開発用の共通サービス
└── .env.example           # ローカル環境変数のひな形
```

## Tool Placement

- npm: `frontend/package.json`
- Poetry: `backend/pyproject.toml`
- Terraform: `infra/terraform/`
- Docker Compose: ルート `docker-compose.yml`

## Quick Start

### 1. 環境変数を用意する

```bash
cp .env.example .env
```

### 2. ローカル依存サービスを起動する

```bash
docker compose up -d db
```

### 3. Frontend の依存関係を導入する

```bash
cd frontend
npm install
```

### 4. Backend の依存関係を導入する

```bash
cd backend
poetry install
```

## Local Development Flow

- Frontend 実装は `frontend/` 配下で進めます
- Backend 実装は `backend/` 配下で進めます
- ローカル DB はルート `docker-compose.yml` で管理します
- Infrastructure は `infra/terraform/` 配下で `dev` / `prod` を分離します
- 詳細な実装責務は `docs/architecture/*.md` を参照します

## Current Bootstrap Status

この issue ではモノレポの配置規約と開発導線のみを整えています。React SPA 本体、Django / DRF 本体、Terraform の実リソース定義は後続 issue で追加します。
