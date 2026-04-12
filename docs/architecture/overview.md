# Kabi Chat Architecture Overview

## Summary

Kabi Chat は、Markdown + TeX を前提にした軽量チャットツールです。MVP では「高速な投稿体験」「raw/view の即時切替」「workspace 単位の文脈共有」を成立させることを主目的とし、リアルタイム同期や高度な運用は将来拡張として扱います。

このリポジトリはモノレポ構成を前提とし、以下の技術スタックを採用します。

- Frontend: React, npm
- Backend: Django, Django REST Framework, Poetry, Docker Compose
- Infrastructure: Terraform, AWS
- Authentication: Discord OAuth2 login, JWT
- Database: PostgreSQL

## System Context

システムは React SPA、Django/DRF API、PostgreSQL、Discord OAuth2、AWS 上の実行基盤で構成します。

1. ユーザーは React SPA にアクセスする
2. 認証が必要な場合は Discord OAuth2 でログインする
3. Backend は Discord の認可結果を検証し、アプリ内 User を作成または更新する
4. Backend は JWT を発行し、Frontend はそれを用いて API を呼び出す
5. Frontend は workspace / channel / message / macro のデータを取得し、Markdown + TeX を描画する

## Responsibility Boundaries

### Frontend

- SPA の画面遷移と UI 状態管理
- message 入力、message 一覧表示、raw/view 切替
- Markdown + TeX のレンダリング
- JWT を用いた API 呼び出し

### Backend

- 認証と認可
- workspace / channel / message / macro の保存と整合性管理
- API 提供
- Discord login callback の処理

### Infrastructure

- AWS リソースの構築と環境分離
- コンテナ実行基盤、データベース、ネットワーク、シークレット配線
- 開発環境と本番環境の責務分離

## Core Domain

MVP で扱う主要な論理エンティティは以下です。

- User
- Workspace
- Channel
- Message
- MacroDefinition

マクロは `global`、`workspace`、`channel` の 3 スコープを持ち、優先順位は `channel > workspace > global` とします。

## Non-Functional Requirements

- ブラウザで利用できる SPA とする
- 投稿と raw/view 切替は低遅延を重視する
- TeX 描画は KaTeX を基本とし、再レンダリングを最小化する
- MVP ではモバイル最適化を必須としない
- 開発環境は Docker Compose により再現可能とする
- IaC は Terraform で管理する

## Interfaces

公開インターフェースとして以下を定義します。

- Auth API
  - `GET /auth/discord/login`
  - `GET /auth/discord/callback`
  - `GET /auth/me`
  - `POST /auth/token/refresh`
  - `POST /auth/logout`
- Application API
  - `/workspaces`
  - `/channels`
  - `/messages`
  - `/macros`

詳細は以下を参照します。

- [frontend.md](/home/void_kyun/kabi-chat/docs/architecture/frontend.md)
- [backend.md](/home/void_kyun/kabi-chat/docs/architecture/backend.md)
- [auth.md](/home/void_kyun/kabi-chat/docs/architecture/auth.md)
- [infra.md](/home/void_kyun/kabi-chat/docs/architecture/infra.md)

## Future Extensions

MVP では採用しないが、設計上の拡張余地として以下を持たせます。

- WebSocket によるリアルタイム同期
- マルチユーザー権限管理の強化
- マクロ定義のバージョン管理
- split view や全体 raw/view 切替
- 監視、監査ログ、CI/CD の強化
