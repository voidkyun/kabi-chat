import { useMemo, useState } from "react";

import { useAuth } from "./auth-context";

export function AuthScreen() {
  const auth = useAuth();
  const [tokenInput, setTokenInput] = useState("");
  const canSubmitToken = useMemo(
    () => auth.status !== "loading" && tokenInput.trim().length > 0,
    [auth.status, tokenInput],
  );

  const handleTokenSubmit = async (event) => {
    event.preventDefault();
    await auth.loginWithAccessToken(tokenInput.trim());
  };

  return (
    <div className="auth-shell">
      <section className="auth-card">
        <p className="eyebrow">Frontend MVP</p>
        <h1>Kabi Chat</h1>
        <p className="auth-copy">
          React SPA の入口です。認証導線と、認証後に workspace / channel / message /
          macro を並べるメイン画面骨格をここから確認できます。
        </p>

        <div className="auth-actions">
          <button
            className="primary-button"
            type="button"
            onClick={auth.startDiscordLogin}
            disabled={auth.status === "loading"}
          >
            Discord OAuth を開始
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={auth.useDemoSession}
            disabled={auth.status === "loading"}
          >
            デモ状態で確認
          </button>
        </div>

        <form className="token-form" onSubmit={handleTokenSubmit}>
          <label className="token-form__label" htmlFor="access-token">
            access token から状態を初期化
          </label>
          <textarea
            id="access-token"
            className="token-form__input"
            value={tokenInput}
            onChange={(event) => setTokenInput(event.target.value)}
            placeholder="Backend の /auth/discord/callback または /auth/token/refresh で取得した access token"
            rows={4}
          />
          <button className="secondary-button" type="submit" disabled={!canSubmitToken}>
            /auth/me で接続確認
          </button>
        </form>

        <div className="auth-hints">
          <div className="auth-hints__item">
            <h2>Auth state</h2>
            <p>ログイン状態、現在ユーザー、access token の寿命管理を分離しています。</p>
          </div>
          <div className="auth-hints__item">
            <h2>Server state</h2>
            <p>workspace / channel / message / macro を API またはデモデータから取得します。</p>
          </div>
          <div className="auth-hints__item">
            <h2>UI state</h2>
            <p>選択中 workspace / channel、raw-view 切替、composer 入力を保持します。</p>
          </div>
        </div>

        {auth.error ? <p className="inline-error">{auth.error}</p> : null}
      </section>
    </div>
  );
}
