# Backend Architecture

## Summary

Backend は Django と Django REST Framework を採用し、Poetry で依存管理、Docker Compose でローカル開発環境を構成します。主責務は、認証、認可、データ保存、API 提供、ドメイン整合性の維持です。

## Application Responsibilities

Backend は以下を担当します。

- Discord OAuth2 callback の受信とユーザー同定
- JWT の発行、更新、失効
- workspace / channel / message / macro の CRUD
- 権限制御
- PostgreSQL への永続化

Markdown や TeX の最終レンダリングは Frontend の責務とし、Backend はレンダリング前のデータを返します。

## Django App Boundaries

実装時は以下の責務分割を前提とします。

- `auth`
  - Discord login
  - JWT 発行と refresh
  - current user 取得
- `workspaces`
  - workspace 作成、取得、参加権限
- `channels`
  - workspace 配下の channel 管理
- `messages`
  - message 投稿、一覧取得
- `macros`
  - global / workspace / channel macro の取得と更新

配置先は `backend/` を既定とし、Poetry 関連ファイルはこのディレクトリ直下に置きます。Django app は `backend/apps/` 配下に配置する前提とします。

## Domain Model

主要エンティティは以下です。

### User

- Discord account と紐づくアプリケーション利用者
- 表示名、アイコン URL、Discord 識別子を保持する
- Django 標準 user と auth app の profile により管理する

### Workspace

- チャット空間の最上位単位
- 設定と参加権限の境界になる

### Channel

- workspace 配下の会話単位
- message 履歴を保持する

### Message

- channel に所属する投稿データ
- 本文、投稿者、投稿時刻を保持する

### MacroDefinition

- TeX macro 定義
- `global`、`workspace`、`channel` のいずれかに紐づく

## API Design

公開 API は以下のカテゴリを持ちます。

- Auth API
  - `GET /auth/discord/login`
  - `GET /auth/discord/callback`
  - `GET /auth/me`
  - `POST /auth/token/refresh`
  - `POST /auth/logout`
- Workspace API
  - `GET /workspaces/`
  - `POST /workspaces/`
  - `GET /workspaces/{id}/`
  - `PATCH /workspaces/{id}/`
- Channel API
  - `GET /channels/?workspace_id={workspace_id}`
  - `POST /channels/`
  - `GET /channels/{id}/`
  - `PATCH /channels/{id}/`
- Message API
  - `GET /messages/?channel_id={channel_id}`
  - `POST /messages/`
- Macro API
  - `GET /macros/`
  - `GET /macros/?effective=true&workspace_id={workspace_id}`
  - `GET /macros/?effective=true&channel_id={channel_id}`
    `workspace_id` と `channel_id` を同時に指定する場合は、`channel` がその `workspace` 配下に属している必要があります。不整合な組み合わせは `400` とします。
  - `POST /macros/`
  - `PATCH /macros/{id}/`

MVP の payload は以下を前提にします。

- Workspace
  - `name`, `description`, `member_ids`
- Channel
  - `workspace_id`, `name`, `topic`
- Message
  - `channel_id`, `body`
- MacroDefinition
  - `name`, `definition`, `scope`, `workspace_id`, `channel_id`

macro の `effective=true` は Frontend がそのまま利用できる解決済み一覧を返し、優先順位は `channel > workspace > global` とします。

DRF では以下を分離します。

- Serializer: 入出力の検証と整形
- View / ViewSet: HTTP ハンドリング
- Permission: workspace / macro の操作可否
- Service layer or domain helper: Discord 認証や token 発行などの業務ロジック

Bootstrap 段階の DRF 既定 permission は `IsAuthenticated` とし、公開 endpoint は `healthz` と Discord OAuth の開始 / callback のみを個別に許可します。

refresh token を `HttpOnly` cookie で扱う前提の `POST /auth/token/refresh` と `POST /auth/logout` は、access token なしでも到達できる endpoint として個別に許可します。

MVP の最低限の権限制御は以下です。

- workspace member は workspace / channel / message / scoped macro を参照できる
- workspace owner は workspace 更新、channel 更新、workspace / channel macro 更新を行える
- global macro の更新は staff user に限定する

## Local Development

ローカル環境は Docker Compose で構成します。

- `app`
  - Django / DRF アプリケーション
- `db`
  - PostgreSQL

必要に応じて reverse proxy や mail mock は後続で追加可能としますが、MVP 必須には含めません。

Backend の `python` 実行はホストではなく app コンテナ経由を前提とします。`manage.py` や `pytest` は `docker compose exec app ...` で実行します。

## Non-Functional Concerns

- API はシンプルな REST を優先する
- MVP ではリアルタイム同期を必須にしない
- DB 整合性と権限制御を優先し、描画最適化は Frontend に委ねる
- 本番運用を見据えて PostgreSQL を採用する
