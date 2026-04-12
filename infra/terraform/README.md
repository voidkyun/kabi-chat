# Terraform Workspace

`infra/terraform/` は AWS 向け Terraform 定義を配置する領域です。

## Directory Intent

- `environments/dev/`
  - 開発環境向け entrypoint
- `environments/prod/`
  - 本番環境向け entrypoint
- `modules/`
  - 環境間で共有する module

MVP の実装詳細は `docs/architecture/infra.md` を参照してください。
