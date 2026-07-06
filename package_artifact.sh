#!/usr/bin/env bash
# Package the ReproBreak artifact for archival upload (e.g., Zenodo).
#
# Produces in dist/:
#   reprobreak-code.zip   code + README (the only markdown inside the zip)
#   ReproBreak-db.zip     the SQLite dataset (from data/ReproBreak.db)
#   README.md, REQUIREMENTS.md, STATUS.md, EXTENDING.md, ARTIFACT_ABSTRACT.md
#                         artifact documentation, as standalone files (the
#                         README copy has no logo and its repo-relative
#                         references rewritten to ReproBreak/)
#   <paper>.pdf           author version of the paper (if present in the root)
#   SHA256SUMS.txt        checksums of the files above
set -euo pipefail
cd "$(dirname "$0")"

DIST=dist
rm -rf "$DIST"
mkdir -p "$DIST"

echo "Packaging code..."
zip -q -r "$DIST/reprobreak-code.zip" . \
  -x ".git/*" -x ".venv/*" -x "repos/*" -x "output/*" -x "data/*" \
  -x "dist/*" -x "__pycache__/*" -x "*/__pycache__/*" -x "*.pyc" \
  -x ".DS_Store" -x "*/.DS_Store" -x ".idea/*" -x "*.pdf" -x "workspace/*" \
  -x "REQUIREMENTS.md" -x "STATUS.md" -x "EXTENDING.md" -x "ARTIFACT_ABSTRACT.md"

echo "Copying artifact documentation..."
cp REQUIREMENTS.md STATUS.md EXTENDING.md ARTIFACT_ABSTRACT.md "$DIST/"

# Standalone README copy: the logo block is dropped (it cannot render on the
# Zenodo record page) and repo-relative references are rewritten to the
# ReproBreak/ folder that unzipping reprobreak-code.zip creates. The README
# inside the zip keeps the original content.
sed '1,/^---$/d' README.md | sed '/./,$!d' | sed \
  -e 's|](Dockerfile.artifact)|](ReproBreak/Dockerfile.artifact)|g' \
  -e 's|](database/schema.sql)|](ReproBreak/database/schema.sql)|g' \
  -e 's|](LICENSE)|](ReproBreak/LICENSE)|g' \
  -e 's|`data/ReproBreak.db`, downloaded separately|`ReproBreak/data/ReproBreak.db`, downloaded separately|' \
  -e 's|`data/ReproBreak.db` unpacked|`ReproBreak/data/ReproBreak.db` unpacked|' \
  > "$DIST/README.md"

echo "Packaging database (this can take a few minutes)..."
if [ -f data/ReproBreak.db ]; then
  zip -q -j "$DIST/ReproBreak-db.zip" data/ReproBreak.db
else
  echo "WARNING: data/ReproBreak.db not found; skipping database packaging."
fi

pdf=$(ls ./*.pdf 2>/dev/null | head -1 || true)
if [ -n "$pdf" ]; then
  echo "Including paper PDF: $pdf"
  cp "$pdf" "$DIST/"
fi

echo "Computing checksums..."
if command -v sha256sum >/dev/null 2>&1; then
  (cd "$DIST" && sha256sum ./* > SHA256SUMS.txt)
else
  (cd "$DIST" && shasum -a 256 ./* > SHA256SUMS.txt)
fi

echo
echo "Artifact files ready in $DIST/:"
ls -lh "$DIST"
cat <<'EOF'

Next step: upload all files from dist/ to a new Zenodo record at
https://zenodo.org/uploads/new, fill in the metadata (title, authors,
MIT license), and publish.
EOF
