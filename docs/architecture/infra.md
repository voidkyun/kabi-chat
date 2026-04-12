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
  - private subnet
  - security group
- Delivery
  - ALB
  - DNS and TLS termination
- Compute
  - ECS cluster
  - Fargate service for Backend
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
