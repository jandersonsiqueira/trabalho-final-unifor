#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source config/tools.env
mkdir -p .work reports
if [[ ! -d .work/VAmPI/.git ]]; then
  git clone https://github.com/erev0s/VAmPI.git .work/VAmPI
fi
if [[ -n "$(git -C .work/VAmPI status --porcelain)" ]]; then
  echo 'VAmPI possui alteracoes locais; use uma copia limpa em .work/VAmPI.' >&2
  exit 1
fi
git -C .work/VAmPI checkout --detach "$VAMPI_COMMIT"
test "$(git -C .work/VAmPI rev-parse HEAD)" = "$VAMPI_COMMIT"
echo "VAmPI: $VAMPI_COMMIT"

