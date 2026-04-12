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
  - workspace 一覧、詳細、作成、更新
- Channel API
  - channel 一覧、作成、更新
- Message API
  - message 一覧、投稿
- Macro API
  - macro 一覧、取得、更新

DRF では以下を分離します。

- Serializer: 入出力の検証と整形
- View / ViewSet: HTTP ハンドリング
- Permission: workspace / macro の操作可否
- Service layer or domain helper: Discord 認証や token 発行などの業務ロジック

## Local Development

ローカル環境は Docker Compose で構成します。

- `app`
  - Django / DRF アプリケーション
- `db`
  - PostgreSQL

必要に応じて reverse proxy や mail mock は後続で追加可能としますが、MVP 必須には含めません。

## Non-Functional Concerns

- API はシンプルな REST を優先する
- MVP ではリアルタイム同期を必須にしない
- DB 整合性と権限制御を優先し、描画最適化は Frontend に委ねる
- 本番運用を見据えて PostgreSQL を採用する
