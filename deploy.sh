#!/bin/bash
set -e

NAS_USER="selmer"
NAS_HOST="192.168.68.115"
NAS_PATH="/volume2/docker/litterbox"

echo "🐱 Litterbox deploy starting..."

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm run build
cd ..

# Commit and push if there are changes
if [[ -n $(git status --porcelain) ]]; then
  echo "📝 Committing changes..."
  git add -A
  git commit -m "${1:-deploy: update}"
  git push
else
  echo "✓ No local changes to commit"
  git push 2>/dev/null || true
fi

# Deploy to NAS
echo "🚀 Deploying to NAS..."
ssh "$NAS_USER@$NAS_HOST" "
  cd $NAS_PATH &&
  git pull &&
  sudo docker compose up --build -d
"

echo "✅ Deploy complete! http://$NAS_HOST:8001"

