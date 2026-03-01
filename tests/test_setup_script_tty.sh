#!/usr/bin/env bash
set -euo pipefail

# TTY integration check for setup.sh interactive redaction path.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

cp "$ROOT_DIR/setup.sh" "$TMP_DIR/setup.sh"
cp "$ROOT_DIR/.env.template" "$TMP_DIR/.env.template"
chmod +x "$TMP_DIR/setup.sh"
cat > "$TMP_DIR/main.py" <<'PY'
print("ok")
PY

cat > "$TMP_DIR/.env" <<'ENV'
212_API_KEY_ID=ABCD1234
212_API_KEY_SECRET=SECRETVALUE
212_API_BASE_DEMO_URL=https://demo.trading212.com/api/v0/
212_API_BASE_LIVE_URL=https://live.trading212.com/api/v0/
ENV

cd "$TMP_DIR"
ORIGINAL_ENV="$(cat .env)"

# Use script(1) so setup.sh sees a TTY; answer "n" at overwrite prompt.
printf 'n\n' | script -q /dev/null ./setup.sh --skip-install --skip-validation --update-claude-config skip > run.log 2>&1 || true

if ! grep -q "Current .env values (redacted):" run.log; then
  echo "Missing redacted preview heading"
  cat run.log
  exit 1
fi

if ! grep -q "212_API_KEY_ID=AB\*\*\*34" run.log; then
  echo "Missing redacted API key"
  cat run.log
  exit 1
fi

if ! grep -q "212_API_KEY_SECRET=SE\*\*\*UE" run.log; then
  echo "Missing redacted API secret"
  cat run.log
  exit 1
fi

CURRENT_ENV="$(cat .env)"
if [ "$CURRENT_ENV" != "$ORIGINAL_ENV" ]; then
  echo ".env should remain unchanged when answering no"
  echo "Before:"
  echo "$ORIGINAL_ENV"
  echo "After:"
  echo "$CURRENT_ENV"
  exit 1
fi

echo "TTY setup script test passed"
