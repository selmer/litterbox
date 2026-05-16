#!/bin/bash
set -euo pipefail

COMMAND="${1:-deploy}"
NAS_USER="${NAS_USER:-selmer}"
NAS_HOST="${NAS_HOST:-192.168.68.115}"
NAS_PATH="${NAS_PATH:-/volume2/docker/litterbox}"
ALLOW_DIRTY_DEPLOY="${ALLOW_DIRTY_DEPLOY:-false}"

validate() {
  echo "Installing backend dependencies..."
  python3 -m pip install -r requirements.txt -q

  echo "Running backend tests..."
  python3 -m pytest tests/ -v

  echo "Installing frontend dependencies..."
  (cd frontend && npm ci)

  echo "Running frontend lint..."
  (cd frontend && npm run lint)

  echo "Running frontend tests..."
  (cd frontend && npm test)

  echo "Building frontend..."
  (cd frontend && npm run build)
}

case "$COMMAND" in
  validate)
    validate
    echo "Validation complete"
    ;;
  deploy)
    echo "Litterbox deploy starting..."
    git pull --ff-only

    if [[ -n "$(git status --porcelain)" && "$ALLOW_DIRTY_DEPLOY" != "true" ]]; then
      echo "Refusing to deploy with local changes. Commit them first, or set ALLOW_DIRTY_DEPLOY=true."
      exit 1
    fi

    validate

    echo "Pushing current branch..."
    git push

    echo "Deploying to NAS..."
    ssh "$NAS_USER@$NAS_HOST" "
      cd $NAS_PATH &&
      git pull --ff-only &&
      sudo docker compose up --build -d
    "

    echo "Deploy complete: http://$NAS_HOST:8001"
    ;;
  *)
    echo "Usage: $0 [validate|deploy]"
    exit 2
    ;;
esac
