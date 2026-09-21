#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source config/tools.env
mkdir -p reports
test "$(git -C .work/VAmPI rev-parse HEAD)" = "$VAMPI_COMMIT"
case "${1:-}" in
  sast)
    rm -f reports/semgrep.sarif reports/sast-commit.txt
    docker run --rm -v "$PWD/.work/VAmPI:/src:ro" -v "$PWD/reports:/reports" \
      -w /src "$SEMGREP_IMAGE" semgrep scan --config=auto --metrics=auto \
      --disable-version-check --strict --sarif --output /reports/semgrep.sarif . \
      2>&1 | tee reports/semgrep.log
    ;;
  source)
    rm -f reports/sbom.json reports/source-commit.txt
    docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e CDXGEN_TEMP_DIR=/tmp \
      -v "$PWD/.work/VAmPI:/src" -v "$PWD/reports:/reports" \
      -w /src --entrypoint env "$CDXGEN_IMAGE" -u NODE_PATH -u SWIFT_SIGNING_KEY \
      cdxgen -t python --spec-version 1.6 --fail-on-error \
      --project-name VAmPI --project-version "$VAMPI_COMMIT" \
      -o /reports/sbom.json /src 2>&1 | tee reports/cdxgen-source.log
    ;;
  build)
    docker build --tag "vampi-lab:$VAMPI_COMMIT" .work/VAmPI \
      2>&1 | tee reports/image-build.log
    docker image inspect "vampi-lab:$VAMPI_COMMIT" \
      --format '{{.Id}}' > reports/image-id.txt
    ;;
  image)
    rm -f reports/sbom-image.json reports/image-commit.txt
    mkdir -p .work/images
    docker save "vampi-lab:$VAMPI_COMMIT" > .work/images/vampi-image.tar
    docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -e CDXGEN_TEMP_DIR=/tmp \
      -v "$PWD/.work/images:/images:ro" \
      -v "$PWD/reports:/reports" --entrypoint env "$CDXGEN_IMAGE" \
      -u NODE_PATH -u SWIFT_SIGNING_KEY cdxgen -t docker \
      --spec-version 1.6 --fail-on-error --project-name VAmPI-image \
      --component-type library --component-type application --component-type framework \
      --component-type container --component-type operating-system --component-type file \
      --project-version "$VAMPI_COMMIT" \
      -o /reports/sbom-image.json /images/vampi-image.tar \
      2>&1 | tee reports/cdxgen-image.log
    ;;
  *) echo 'Uso: bash scripts/scan.sh {sast|source|build|image}' >&2; exit 2 ;;
esac
printf '%s\n' "$VAMPI_COMMIT" > "reports/${1}-commit.txt"
