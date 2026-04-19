# Autodev Workflow

## 目的

このワークフローは、ユーザーの提案を起点に、AgentがGitHub上でのIssue管理、実装、レビュー、デプロイ、報告までを自律的に行うためのものである。

対象はモノリポのWebアプリケーションであり、現在は単一Lightsailインスタンス上で稼働するアーリーアクセス環境を前提とする。

---

## 前提理解

Agentは以下を前提として理解すること。

- リポジトリはモノリポである
- `infra/terraform/environments/prod` が本番相当環境である
- `infra/terraform/environments/dev` は一時検証環境であり、常設ではない
- Lightsail単一インスタンス構成であり、スケーラビリティよりもシンプルさを優先している
- CI/CDにより main マージ後に自動デプロイされる

---

## タスク分解

ユーザー提案を受けたら、まず以下の粒度で分解する。

- feature / bugfix / refactor の分類
- UI / API / domain / infra のどこに影響するか
- 変更対象ディレクトリ
- 影響範囲（既存機能、データ、外部I/O）

分解結果は内部的に保持し、必要に応じてIssueとして表現する。

---

## Issue戦略

実装前に、必要な作業単位がすべてIssueとして表現されている状態を作る。

- 1 Issue = 1責務
- 実装可能な粒度に分割する
- 依存関係がある場合は明示する
- ラベル例:
  - `feature`
  - `bug`
  - `refactor`
  - `infra`
  - `breaking-change`（承認必須）

既存Issueと重複する場合は新規作成せず統合する。

---

## 実装方針

### 基本

- 既存のコードスタイルに従う
- 最小変更で目的を達成する
- 不要な抽象化を導入しない
- 既存設計との整合性を優先する

### モノリポ特有ルール

- 変更対象の境界をまたぐ場合は、依存方向を壊さない
- domain層のロジックをUI層に漏らさない
- API契約変更は breaking-change として扱う

---

## テスト・検証

変更内容に応じて、以下を適切に実施する。

- unit test
- integration test
- APIの疎通確認
- UIの基本動作確認

少なくとも以下は必須。

- 既存テストが壊れていないこと
- 追加機能の最低限の正常系が通ること

変更対象に対応するCIが未整備の場合は、その事実を既知のリスクとしてPRと最終報告に明記する。変更の性質上必要であり、影響範囲が限定的で承認必須条件に当たらない場合は、先に最小限のCI導線を追加してよい。

---

## Pull Request

PRには必ず以下を含める。

- 変更内容
- 変更理由
- 影響範囲
- 検証方法
- 未対応事項（あれば）

初回PR、修正PR、review指摘対応PR、follow-up PR を区別せず、すべて同じレビュー・検証・merge 判定ルールを適用する。

---

## 自己レビュー

自己レビューは必ず `code-review.md` のルールに従う。

- 観点ごとにSubAgentをspawnする
- 指摘はすべて解消または意図を説明する
- follow-up PR を含め、main にマージする前のPRごとに必ず独立して実施する

---

## merge判定

以下をすべて満たす場合のみ merge を許可する。

- 変更対象に対応するCI / check run が成功している
- reviewで重大指摘が残っていない
- 承認必須条件に該当しない
- rollback可能である

merge 判定では GitHub の check runs を source of truth として扱う。legacy status API が空または `pending` のままでも、必要な check run の完了状態を別途確認して判定する。

---

## デプロイ後チェック

可能な範囲で以下を確認する。

- アプリが起動している
- 主要エンドポイントが応答する
- UIが致命的に壊れていない

---

## パッチノート

最終報告は以下形式。

- Summary
- Changes
- Impact
- Validation
- Known Issues / Next Steps

Known Issues / Next Steps には、未整備のCI、残存リスク、依存上の懸念があれば必ず記載する。

---

## 禁止事項

以下は自律実行してはならない。

- Terraformのapply（特にprod）
- Lightsail設定変更
- ポート開放設定変更
- ssh_allowed_cidrs変更
- Secret / 認証情報の変更
- 外部サービス設定変更
