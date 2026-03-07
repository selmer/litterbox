#!/bin/bash
set -e

NAS_USER="selmer"
NAS_HOST="192.168.68.115"
NAS_PATH="/volume2/docker/litterbox"

echo "🐱 Litterbox deploy starting..."
# pulling git data
echo "pulling git data"
git pull

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q

# Run tests before deploying — abort if any test fails
echo "🧪 Running tests..."
python3 -m pytest tests/ -v
echo "✅ All tests passed"

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm install
sudo chown -R $(whoami) node_modules
npm run build
cd ..

# Commit and push if there are changes
if [[ -n $(git status --porcelain) ]]; then
  echo "📝 Committing changes..."
  # Use 'git add -u' instead of 'git add -A' to only stage already-tracked files,
  # preventing accidental staging of untracked secrets, .env files, or binaries.
  git add -u
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

