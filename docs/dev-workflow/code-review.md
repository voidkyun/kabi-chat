# Code Review Guideline

## 目的

実装時のバイアス（自己正当化、前提依存）を排除し、差分ベースで客観的に品質を担保する。

---

## 基本戦略

レビューは必ずSubAgentで実行する。

- 実装背景は最小限にする
- 差分（PR）を主対象とする
- 必要に応じて周辺コードは読む
- 意図の善意は仮定しない

---

## Reviewプロセス

親Agentは以下のSubAgentをspawnする。

1. correctness reviewer
2. security reviewer
3. test reviewer
4. maintainability reviewer

必要に応じて追加:

- performance reviewer
- concurrency reviewer

初回PR、修正PR、follow-up PR を区別せず、main にマージする前のPRごとにこのレビューを独立して実行する。

---

## 共通ルール

- 指摘はすべて actionable にする
- severity をつける
  - critical
  - high
  - medium
  - low
- 推測は避け、コードから読み取れる事実ベースで書く

---

## 観点定義

### 1. correctness

- null / undefined の扱い
- 境界条件
- off-by-one
- エラーハンドリング漏れ
- 既存ロジックとの不整合

---

### 2. security

- 認証/認可の抜け
- 入力値検証不足
- injectionリスク
- 機密情報の露出
- 不要な公開エンドポイント

---

### 3. test

- 新規ロジックにテストがあるか
- 重要分岐がカバーされているか
- 回帰防止になっているか
- failureケースが考慮されているか
- 変更対象に対応するCIが存在するか
- 対象PRで必要なCI / check run が実行されているか

---

### 4. maintainability

- 命名が意図を表しているか
- 責務が分離されているか
- 重複コードがないか
- 過剰な抽象化がないか
- コメントが必要な箇所に存在するか

---

### 5. performance（必要時）

- 無駄なループ
- N+1問題
- 重いI/O
- キャッシュ可能な処理

---

## 出力フォーマット

各SubAgentは以下形式で返す。

```

[severity] (category) file:line
description

suggestion

```

例:

```

[high] (correctness) user_service.ts:42
nullチェックがなく、undefined参照の可能性がある

userが存在しない場合のハンドリングを追加する

```

---

## 集約ルール

親Agentは以下を行う。

- 重複指摘の統合
- severity順に並べ替え
- 修正要否の判断

CI coverage gap や必要な check run の欠落も、merge を止めるべき事実であれば actionable finding として扱ってよい。

---

## mergeブロック条件

以下が1つでも存在する場合、mergeしてはならない。

- critical または high の未解決指摘
- テスト不足による不確実性
- セキュリティリスク
- 必要な check run の未完了または未実行

---

## 例外

以下は許容される場合がある。

- low severity の未解決（理由が明確な場合）
- 技術的負債として意図的に残すもの（明示されている場合）
