# Terraform Workspace

`infra/terraform/` は AWS 向け Terraform 定義を配置する領域です。

## Directory Intent

- `environments/dev/`
  - 検証用または一時環境向け entrypoint
- `environments/prod/`
  - アーリーアクセス利用者向け常設環境 entrypoint
- `modules/`
  - 環境間で共有する module

## Current Modules

- `modules/lightsail_early_access/`
  - 単一 Lightsail instance
  - static IP
  - public port 制御
  - auto snapshot

## Current Environments

- `environments/prod/`
  - 常設アーリーアクセス環境
  - 80 / 443 を全公開
  - 22 は `ssh_allowed_cidrs` に制限
- `environments/dev/`
  - 一時検証環境
  - static IP / snapshot は省略
  - 22 と 80 のみ必要時に公開

アーリーアクセス中は `prod` のみを常設対象とし、`dev` は必要時 apply を前提とします。MVP の実装詳細は `docs/architecture/infra.md` を参照してください。
