# Backend Development Workflow

## Summary

Backend の開発作業は、原則としてリポジトリルートで `docker compose` から始めます。ホストの Python / pip / Poetry は使わず、Django の管理コマンド、テスト、依存追加は app コンテナ経由で実行します。

LLM に手順を渡すときも、Backend 関連コマンドは `docker compose ...` の形で書くことを前提にします。

## Basic Policy

- Backend の作業ディレクトリは app コンテナ内の `/app`
- 日常的なコマンド実行は `docker compose exec app ...`
- app コンテナが未起動の状態で単発実行したい場合は `docker compose run --rm app ...`
- `python`, `pytest`, `poetry` をホストで直接実行しない

複数コマンドをまとめて試すときは `docker compose exec app sh` でコンテナ内シェルに入ってよいですが、手順書やレビューコメントでは `docker compose ...` から始まる例を優先します。

## Startup

`.env` が必要な場合は、リポジトリルートで `.env.example` を元に `.env` を用意します。

通常の起動手順は以下です。

```bash
docker compose up --build -d db app
docker compose ps
docker compose logs -f app
```

app コンテナは起動時に `python manage.py migrate --noinput` を実行してから `runserver` を立ち上げます。

## Daily Commands

開発中によく使うコマンドは以下です。

```bash
docker compose exec app python manage.py check
docker compose exec app python manage.py shell
docker compose exec app python manage.py showmigrations
docker compose exec app pytest
docker compose exec app pytest apps/auth
docker compose exec app pytest apps/auth -k callback
```

app コンテナがまだ起動していない状態で単発実行したい場合は、以下のように `run --rm` を使います。

```bash
docker compose run --rm app python manage.py check
docker compose run --rm app pytest
```

## Model Change Workflow

モデル変更時は、migration 作成と適用をコンテナ経由で行います。

```bash
docker compose exec app python manage.py makemigrations
docker compose exec app python manage.py migrate
docker compose exec app python manage.py showmigrations
```

特定 app の migration を作る場合は app 名を明示します。

```bash
docker compose exec app python manage.py makemigrations auth
```

## Dependency Change Workflow

依存追加も app コンテナで行います。

```bash
docker compose exec app poetry add <package>
docker compose exec app poetry add --group dev <package>
```

ただし、依存は Docker image に入る前提なので、`poetry add` の後は app image を rebuild して起動し直します。

```bash
docker compose build app
docker compose up -d app
docker compose exec app pytest
```

依存追加後に再 build しないと、コンテナ再作成時に追加したライブラリが消えたように見えるので注意してください。

## Debugging

ログ確認とコンテナ内シェルは以下を使います。

```bash
docker compose logs -f app
docker compose exec app sh
docker compose exec db sh
```

DB 接続まわりを確認したいときは、まず app と db の両方が起動しているかを `docker compose ps` で確認します。

## Shutdown

作業終了時は以下を使います。

```bash
docker compose down
```

PostgreSQL のデータを消したい場合だけ volume を明示的に落としますが、通常作業では不要です。
