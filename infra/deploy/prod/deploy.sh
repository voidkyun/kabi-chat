#!/bin/sh

set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=$(CDPATH= cd -- "$script_dir/../../.." && pwd)
compose_file="$script_dir/docker-compose.yml"
env_file="${DEPLOY_ENV_FILE:-$script_dir/.env}"

if [ ! -f "$env_file" ]; then
  echo "deploy env file not found: $env_file" >&2
  exit 1
fi

cd "$project_root"

docker compose -f "$compose_file" --env-file "$env_file" build app gateway
docker compose -f "$compose_file" --env-file "$env_file" up -d --remove-orphans
