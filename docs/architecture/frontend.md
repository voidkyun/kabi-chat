# Frontend Architecture

## Summary

Frontend は React ベースの SPA とし、npm をパッケージマネージャ兼ビルド実行基盤として利用します。主責務は、認証導線、workspace / channel / message の閲覧と投稿、raw/view 切替、Markdown + TeX 描画です。

## UI Responsibilities

- Discord login を開始する認証導線を提供する
- workspace 一覧と選択 UI を提供する
- channel 一覧と選択 UI を提供する
- message 一覧表示と message 投稿 UI を提供する
- message ごとの raw/view 切替を提供する
- macro 一覧参照と必要最小限の編集 UI を提供する

MVP ではデスクトップブラウザを主対象とし、モバイル最適化は必須要件に含めません。

## State Model

Frontend の状態は以下に分離します。

- Auth state
  - ログイン状態
  - 現在ユーザー情報
  - access token の有効状態
- Server state
  - workspace 一覧
  - channel 一覧
  - message 一覧
  - macro 定義
- UI state
  - 選択中 workspace
  - 選択中 channel
  - 各 message の raw/view モード
  - message composer の入力内容

## Rendering Strategy

- message 本文は Markdown + TeX として扱う
- TeX 描画は KaTeX を既定とする
- raw モードではレンダリングせず入力文字列をそのまま表示する
- view モードでは Markdown を HTML 化し、その中の数式を描画する
- MathJax fallback は将来拡張として扱う

レンダリング負荷を抑えるため、message 再描画は必要最小限に限定する前提で設計します。

## API Integration

- Backend との通信は DRF が提供する REST API を利用する
- 認証済み API には access token を付与する
- access token 失効時は refresh endpoint で再取得する
- Discord 認証の callback 処理は Backend 側で完結させる

想定 API カテゴリ:

- `/auth/*`
- `/workspaces/*`
- `/channels/*`
- `/messages/*`
- `/macros/*`

## Directory Intent

実装時は以下の責務で構成することを想定します。

- pages or routes
  - 認証完了後のメイン画面
- features
  - auth
  - workspaces
  - channels
  - messages
  - macros
- shared ui
  - layout
  - form
  - renderer

配置先は `frontend/` を既定とし、npm 関連ファイルはこのディレクトリ直下に置きます。

## Extension Points

- WebSocket による message push 配信
- split view 対応
- macro 編集 UI の強化
- message 仮投稿や optimistic update の高度化
