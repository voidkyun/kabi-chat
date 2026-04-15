# Terraform Workspace

`infra/terraform/` は AWS 向け Terraform 定義を配置する領域です。MVP では `dev` / `prod` を分離し、環境ごとの差分は entrypoint 側の変数で吸収します。

## Directory Layout

- `environments/dev/`
  - 開発環境向け entrypoint
  - 小さめの ECS / RDS 構成を前提にする
- `environments/prod/`
  - 本番環境向け entrypoint
  - desired count, DB 保護設定, TLS 前提の差分を持てるようにする
- `modules/network/`
  - VPC, public subnet, private subnet, route table
- `modules/ecr/`
  - Backend image 配布用 ECR repository
- `modules/alb/`
  - ALB, listener, target group, ALB security group
- `modules/ecs_service/`
  - ECS cluster, Fargate service, task definition, app security group, log group
- `modules/rds_postgres/`
  - RDS PostgreSQL, subnet group, DB security group
- `modules/secrets/`
  - Secrets Manager 上の secret container

## Environment Policy

- `dev` と `prod` は別 entrypoint とし、state も分離する
- module は共有し、環境差分は variable と `terraform.tfvars` で表現する
- 共通 naming は `{project}-{environment}-...` を前提にする

## Secret Inventory

MVP で Terraform 管理対象として列挙する secret は以下です。

- `DJANGO_SECRET_KEY`
- `DISCORD_CLIENT_SECRET`
- `JWT_SIGNING_KEY`
- `DATABASE_URL`
- RDS master user password

`modules/secrets/` は application secret の container だけを作成し、値の投入は運用手順または CI/CD 側で行います。RDS master password は `aws_db_instance.manage_master_user_password` により AWS 管理 secret を利用する前提です。

## Local vs Cloud Responsibilities

- `docker-compose.yml`
  - ローカル開発用の app / db 再現
  - `.env` を使ったローカル接続
- `infra/terraform/`
  - AWS 上の VPC, ECS Fargate, ALB, RDS, ECR, Secrets Manager の構築
  - 環境分離とクラウド secret 配線

Docker Compose はローカル開発の再現専用であり、Terraform で管理するクラウド環境の代替ではありません。

MVP の実装詳細は [docs/architecture/infra.md](/home/void_kyun/kabi-chat/docs/architecture/infra.md) を参照してください。
