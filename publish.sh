#!/usr/bin/env bash
set -euo pipefail

# Branch whose raw GitHub URLs are used for README images.
# Override with: RELEASE_BRANCH=master ./publish.sh
RELEASE_BRANCH="${RELEASE_BRANCH:-$(git rev-parse --abbrev-ref HEAD)}"
REPO="Shrivastava-Aditya/boolean-algebra-engine-python"
RAW_BASE="https://raw.githubusercontent.com/${REPO}/${RELEASE_BRANCH}/images/"

echo "Branch : $RELEASE_BRANCH"
echo "Version: $(grep '^version' pyproject.toml | head -1 | cut -d'"' -f2)"

# Patch image URLs in a temp copy of the README so the source file stays clean
cp README.md README.md.bak
sed -i "s|https://raw.githubusercontent.com/${REPO}/[^/]*/images/|${RAW_BASE}|g" README.md

rm -rf dist/ build/
python -m build

# Restore original README
mv README.md.bak README.md

twine upload dist/*
