# Terraform Workspace

`infra/terraform/` は AWS 向け Terraform 定義を配置する領域です。

## Directory Intent

- `environments/dev/`
  - 検証用または一時環境向け entrypoint
- `environments/prod/`
  - アーリーアクセス利用者向け常設環境 entrypoint
- `modules/`
  - 環境間で共有する module

アーリーアクセス中は `prod` のみを常設対象とし、`dev` は必要時 apply を前提とします。MVP の実装詳細は `docs/architecture/infra.md` を参照してください。
