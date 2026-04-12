# Authentication Architecture

## Summary

認証は Discord OAuth2 login を唯一の外部 IdP とし、アプリケーション内の API 認証は JWT で行います。Backend が OAuth2 callback と token 発行を担い、Frontend は access token を利用して API を呼び出します。

## Auth Flow

1. Frontend が `GET /auth/discord/login` を通じてログイン開始 URL を取得またはリダイレクトする
2. ユーザーが Discord 上で認可する
3. Discord は `GET /auth/discord/callback` に認可コードを返す
4. Backend が code と state を検証し、Discord から user 情報を取得する
5. Backend が User を作成または更新する
6. Backend が access token と refresh token を発行する
7. Frontend は `GET /auth/me` を使ってログイン済みユーザー情報を取得する

## Token Strategy

- access token は短命とする
- refresh token は長命とする
- access token は Frontend のメモリ保持を既定とする
- refresh token は `HttpOnly`, `Secure`, `SameSite=Lax` cookie で保持する

refresh は `POST /auth/token/refresh` で行い、logout は `POST /auth/logout` で refresh token を無効化します。

この 2 endpoint は refresh token cookie をもとに処理するため、access token の有無に依存しない設計とします。

## Authorization Boundaries

MVP の認可境界は以下を前提とします。

- workspace 管理者
  - workspace 設定変更
  - workspace macro 編集
  - channel 作成や管理
- 一般参加者
  - message 投稿
  - message 閲覧
  - channel 閲覧
- global macro 管理者
  - global macro の更新

## Error Handling

最低限考慮する失敗ケースは以下です。

- Discord 側で認可拒否された
- callback の `state` が一致しない
- 認可コードが無効または期限切れ
- access token の期限切れ
- refresh token が無効、失効、改ざんされている
- logout 後に refresh を再利用しようとした

これらは Frontend から識別可能な HTTP ステータスとエラーレスポンスで返す前提とします。

## Public Interfaces

- `GET /auth/discord/login`
  - Discord 認証開始
- `GET /auth/discord/callback`
  - Discord callback を受けてログイン完了
- `GET /auth/me`
  - 現在ユーザー情報を返す
- `POST /auth/token/refresh`
  - refresh token により access token を再発行する
- `POST /auth/logout`
  - refresh token を失効させる

## Security Notes

- Discord client secret は Backend と Infrastructure の secret 管理配下に置く
- JWT signing secret または鍵は Infrastructure の secret 管理配下に置く
- Frontend には client secret を置かない
- CSRF, cookie, redirect URI の整合性を環境ごとに管理する
