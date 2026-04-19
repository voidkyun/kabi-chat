# Autodev Skill

## 位置づけ

この文書は `[autodev]` または `autodev` skill の明示利用時に実行する skill を定義する。

- 何を入力として受け取るか
- どの成果物を作るか
- どの順で進めるか
- どこで停止または報告するか

発火条件、禁止事項、merge 条件のようなポリシーは `docs/agent-chat-rule/auto-develop.md` を参照する。  
自己レビューの実施方法は `docs/dev-workflow/code-review.md` を参照する。

## 目的

ユーザーの提案を起点に、GitHub 上の作業整理、実装、検証、レビュー、merge 判定、デプロイ後確認、報告までを一貫したフェーズで進める。

## 前提コンテキスト

この skill は以下を前提として使う。

- リポジトリはモノリポである
- `infra/terraform/environments/prod` が本番相当環境である
- `infra/terraform/environments/dev` は一時検証環境であり、常設ではない
- Lightsail 単一インスタンス構成であり、スケーラビリティよりもシンプルさを優先している
- `main` merge 後に CI/CD で自動デプロイされる

## 入力

この skill が受け取る主な入力は以下。

- `[autodev]` を含むユーザー提案
- `autodev` skill の利用を明示したユーザー提案
- 既存の Issue / Pull Request
- 関連コードと既存ドキュメント
- 変更対象に対応する検証導線

## 出力

この skill が生成または更新する成果物は以下。

- 必要に応じて整理された Issue
- 実装差分
- テスト差分
- Pull Request
- 自己レビュー結果
- merge 可否の判断
- デプロイ後確認結果
- パッチノート形式の最終報告

## フェーズ

### 1. Intake

ユーザー提案をまず以下の軸で分解する。

- feature / bugfix / refactor の分類
- UI / API / domain / infra のどこに影響するか
- 変更対象ディレクトリ
- 既存機能、データ、外部 I/O への影響範囲

この分解結果は以降の Issue 整理、実装範囲、検証範囲の基礎情報として扱う。

### 2. Discovery

実装前に、関連する GitHub とコードベースの状態を確認する。

- 既存 Issue と PR の有無
- 重複または競合する作業の有無
- 既存実装との整合性
- 追加で必要になる検証やドキュメント更新の有無

### 3. Issue Preparation

必要な作業単位が Issue として表現されていない場合は整理する。

- 1 Issue = 1責務
- 実装可能な粒度に分割する
- 依存関係がある場合は明示する
- 既存 Issue と重複する場合は新規作成せず統合する

ラベル例:

- `feature`
- `bug`
- `refactor`
- `infra`
- `breaking-change`

### 4. Implementation

実装では以下を基本とする。

- 既存コードスタイルに従う
- 最小変更で目的を達成する
- 不要な抽象化を導入しない
- 既存設計との整合性を優先する

モノリポでは特に以下を確認する。

- 境界をまたぐ変更でも依存方向を壊さない
- domain 層のロジックを UI 層に漏らさない
- API 契約変更は影響範囲を明示する

### 5. Validation

変更内容に応じて、必要な検証を選択して実施する。

- unit test
- integration test
- API の疎通確認
- UI の基本動作確認
- lint
- typecheck
- build

少なくとも以下は満たす。

- 既存テストが壊れていないこと
- 追加機能の最低限の正常系が通ること

変更対象に対応する CI が未整備な場合は、既知のリスクとして PR と最終報告に明記する。変更の性質上必要で、影響範囲が限定的な場合は最小限の CI 導線追加を先行してよい。

### 6. Pull Request

PR には少なくとも以下を含める。

- 変更内容
- 変更理由
- 影響範囲
- 検証方法
- 未対応事項

修正 PR や follow-up PR であっても、同じ粒度で情報を残す。

### 7. Self Review

自己レビューは必ず `docs/dev-workflow/code-review.md` に従って実施する。

- 観点ごとに SubAgent を spawn する
- 指摘は解消または意図を説明する
- PR ごとに独立して実施する
- review 結果を集約して merge blocker を判断する

### 8. Merge Decision

merge 可否は `docs/agent-chat-rule/auto-develop.md` の条件に従って判断する。

- merge 可能なら、その根拠をユーザーに明示する
- blocker が残るなら、PR を更新して停止する

### 9. Post Deploy Check

merge 後は可能な範囲で以下を確認する。

- アプリが起動している
- 主要エンドポイントが応答する
- UI が致命的に壊れていない

### 10. Patch Notes

最終報告は以下の見出しを基本とする。

- Summary
- Changes
- Impact
- Validation
- Known Issues / Next Steps

`Known Issues / Next Steps` には、未整備の CI、残存リスク、依存上の懸念があれば必ず記載する。

## 停止条件

以下の場合は最後まで進めず、状況を明示して停止する。

- `docs/agent-chat-rule/auto-develop.md` の承認必須条件に該当する
- merge 条件を満たせない blocker が残っている
- 必要な検証が実行できず、リスク評価ができない
- 既存 Issue / PR と競合し、自律的に解消できない
