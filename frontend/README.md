# Frontend Workspace

`frontend/` は React SPA を配置する領域です。

現状は Vite + React ベースの SPA 初期構成を持ち、認証導線、認証後メイン画面骨格、message ごとの raw/view 切替、Markdown + TeX 描画を確認できます。

## Commands

```bash
npm install
npm run dev
npm run build
```

開発サーバーは `http://localhost:5173` で起動し、`/auth`、`/workspaces`、`/channels`、`/messages`、`/macros` を Backend (`http://localhost:8000`) に proxy します。

## Directory Intent

- `src/app/`
  - アプリの composition root
- `src/features/`
  - `auth`, `ui-state`, `server-state`, `workspaces`, `channels`, `messages`, `macros`
- `src/shared/`
  - `api`, `data`

MVP の実装詳細は `docs/architecture/frontend.md` を参照してください。
