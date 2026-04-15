# Infrastructure Architecture

## Summary

Infrastructure は Terraform により AWS 上へ構築します。MVP では React フロントエンドの静的配信、Django/DRF API のコンテナ実行、PostgreSQL の管理、ネットワークとシークレット管理を最小責務とします。

## Target Environment

MVP の既定構成は以下です。

- AWS
- Terraform
- Docker image 配布用 ECR
- Backend 実行基盤は ECS Fargate
- Database は RDS PostgreSQL

## AWS Resource Boundaries

最低限の責務分割は以下です。

- Network
  - VPC
  - public subnet
  - private app subnet
  - private db subnet
  - internet gateway
  - NAT gateway
  - route table
- Delivery
  - ALB
  - DNS and TLS termination
- Compute
  - ECS cluster
  - Fargate service for Backend
  - CloudWatch Logs
  - ECS task execution role
- Data
  - RDS PostgreSQL
- Artifact / Static
  - ECR
  - static asset 配信用ストレージ
- Secrets
  - Django secret key
  - Discord client secret
  - DB credentials
  - JWT signing secret or key

## Deployment Model

- Frontend は静的アセットとして配信する
- Backend はコンテナとしてデプロイする
- Backend は private network 側で DB に接続する
- 外部公開は ALB 経由とする
- Backend image は ECR に push し、ECS task definition から参照する
- app 用 secret は AWS Secrets Manager から注入する

Docker Compose はローカル開発環境の再現用であり、Terraform 管理下のクラウド環境とは明確に分離します。

## Environment Separation

最低限 `dev` と `prod` を分離します。

- `dev`
  - 検証用
  - 小規模構成を許容
- `prod`
  - 本番利用
  - secret, database, network policy を厳格化

Terraform では環境ごとの差分を変数または workspace 相当の仕組みで管理する前提です。

リポジトリ上の配置先は `infra/terraform/` を既定とし、`environments/dev`, `environments/prod`, `modules` の責務で分離します。

Terraform の entrypoint は各環境ディレクトリに置き、共有 module を呼び出す構成とします。

- `environments/dev`
  - 検証用の entrypoint
  - 小さめの task size, desired count, DB class を許容する
- `environments/prod`
  - 本番用の entrypoint
  - desired count, deletion protection, backup retention, TLS を厳格化する
- `modules/network`
  - VPC, subnet, route, NAT
- `modules/alb`
  - public ALB, listener, target group
- `modules/ecs_service`
  - ECS cluster, Fargate service, task definition, log group, app security group
- `modules/rds_postgres`
  - subnet group, DB instance, DB security group
- `modules/ecr`
  - Backend image repository
- `modules/secrets`
  - アプリケーション secret の container

## Secret Management

MVP 時点でクラウド側で管理対象に含める secret は以下です。

- `DJANGO_SECRET_KEY`
- `DISCORD_CLIENT_SECRET`
- `JWT_SIGNING_KEY`
- `DATABASE_URL`
- RDS master user password

`DISCORD_CLIENT_ID` や redirect URI のような秘匿性が低い設定値は通常の環境変数として扱い、Secrets Manager の対象から外します。DB の master password は RDS 管理 secret を使う前提とし、Backend から使う `DATABASE_URL` は application secret として別に保持する前提です。

## Local Development Separation

ローカル開発とクラウド環境の責務は以下のように分離します。

- Docker Compose
  - Backend app と PostgreSQL をローカルで再現する
  - `.env` を読み込み、ローカル接続情報と OAuth 開発設定を保持する
- Terraform
  - AWS の network, ECS, ALB, RDS, ECR, secret container を構築する
  - `dev` / `prod` の state と差分を管理する
  - secret の値そのものではなく、配置先と参照経路を定義する

## Operational Concerns

MVP で最小限考慮する項目:

- シークレットの安全な注入
- ALB 配下のヘルスチェック
- DB バックアップ方針
- デプロイ時の無停止性を意識した構成

将来拡張:

- CloudWatch ベースの監視
- 監査ログ
- CI/CD の自動化
- CDN の追加
