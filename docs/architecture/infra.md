# Infrastructure Architecture

## Summary

Infrastructure は Terraform により AWS 上へ構築します。アーリーアクセス段階では「ユーザー数 10 名以下」「セキュリティ要件は中程度」「月額およそ 20 USD 以下」を前提とし、運用コストよりもシンプルさを優先します。MVP では React フロントエンドの静的配信、Django/DRF API のコンテナ実行、PostgreSQL の管理、公開 HTTPS 導線、シークレット管理を最小責務とします。

## Target Environment

アーリーアクセスの既定構成は以下です。

- AWS
- Terraform
- 常設環境は単一の Lightsail instance
- Frontend はビルド済み静的アセットを同一 instance 上の reverse proxy から配信する
- Backend は同一 instance 上の container として実行する
- Database は同一 instance 上で PostgreSQL を動かし、永続 volume に保存する

ECS Fargate, RDS PostgreSQL, ALB, ECR は将来の拡張候補とし、アーリーアクセスの既定構成からは外します。

## AWS Resource Boundaries

最低限の責務分割は以下です。

- Network
  - Lightsail networking
  - static IP
  - instance firewall
- Delivery
  - reverse proxy
  - DNS record
  - TLS termination
- Compute
  - single Lightsail instance
  - application containers
- Data
  - PostgreSQL data volume
  - snapshot or backup export
- Secrets
  - Django secret key
  - Discord client secret
  - DB credentials
  - JWT signing secret or key
  - admin or deploy access credentials

## Deployment Model

- Frontend は静的アセットとして配信する
- Backend はコンテナとしてデプロイする
- PostgreSQL は同一 host の private container network または localhost でのみ公開する
- 外部公開は instance 上の reverse proxy を経由する
- 公開 endpoint は HTTPS を前提とする

Docker Compose はローカル開発環境の再現用であり、クラウド環境とは compose file や secret の注入経路を分離します。アーリーアクセス中はローカル開発を主とし、クラウド `dev` は常設前提にしません。

配備素材は `infra/deploy/prod/`、Terraform entrypoint は `infra/terraform/environments/{dev,prod}/`、共通 module は `infra/terraform/modules/lightsail_early_access/` を既定とします。

## Environment Separation

最低限 `dev` と `prod` を分離します。

- `dev`
  - 検証用
  - 必要時だけ apply する小規模または一時環境
  - 日常開発は Docker Compose を優先する
- `prod`
  - アーリーアクセス利用者向けの常設環境
  - secret, backup, firewall, HTTPS を必須にする

Terraform では環境ごとの差分を変数または workspace 相当の仕組みで管理する前提です。

リポジトリ上の配置先は `infra/terraform/` を既定とし、`environments/dev`, `environments/prod`, `modules` の責務で分離します。`prod` は常設環境、`dev` は検証用 entrypoint として扱います。

## Operational Concerns

MVP で最小限考慮する項目:

- シークレットを repository に含めず安全に注入する
- PostgreSQL を外部公開しない
- HTTPS 証明書の更新手段を持つ
- DB の snapshot または dump backup 方針を持つ
- instance 障害時に再作成できるよう Terraform と運用手順を分離する

将来拡張:

- ECS Fargate への移行
- RDS PostgreSQL への移行
- ALB や CDN の追加
- CloudWatch ベースの監視
- 監査ログ
- CI/CD の自動化
