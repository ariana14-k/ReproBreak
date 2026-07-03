#!/usr/bin/env bash
# Package the ReproBreak artifact for archival upload (e.g., Zenodo).
#
# Produces in dist/:
#   reprobreak-code.zip   code + documentation
#   ReproBreak-db.zip     the SQLite dataset (from data/ReproBreak.db)
#   <paper>.pdf           author version of the paper (if present in the root)
#   SHA256SUMS.txt        checksums of the files above
set -euo pipefail
cd "$(dirname "$0")"

DIST=dist
rm -rf "$DIST"
mkdir -p "$DIST"

echo "Packaging code..."
# ARTIFACT_ABSTRACT.md is the submission-form content (CfA step 3), not part
# of the reviewed package.
zip -q -r "$DIST/reprobreak-code.zip" . \
  -x ".git/*" -x ".venv/*" -x "repos/*" -x "output/*" -x "data/*" \
  -x "dist/*" -x "__pycache__/*" -x "*/__pycache__/*" -x "*.pyc" \
  -x ".DS_Store" -x "*/.DS_Store" -x ".idea/*" -x "*.pdf" -x "workspace/*" \
  -x "ARTIFACT_ABSTRACT.md"

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

Next steps (Zenodo):
 1. Create a new upload at https://zenodo.org/uploads/new, upload all
    files from dist/, fill in the metadata (title, authors, MIT
    license), and publish. Publishing assigns the DOI.
 2. Insert the published record link into ARTIFACT_ABSTRACT.md
    (Badge and Provenance sections) before submitting it.
 3. Add a Data Availability statement with the DOI to the camera-ready
    version of the paper.
EOF
