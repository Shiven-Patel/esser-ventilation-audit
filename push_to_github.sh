#!/usr/bin/env bash
#
# push_to_github.sh
# -----------------
# Publish this repository to github.com/Shiven-Patel/<REPO>.
#
# Run it from inside the repository directory:
#     bash push_to_github.sh
#
# It needs either the GitHub CLI (`gh`, authenticated) or an existing empty
# repository created by hand at github.com/new. Nothing here handles or stores
# a token; authentication is whatever your machine already has.
#
set -euo pipefail
cd "$(dirname "$0")"

OWNER="Shiven-Patel"
REPO="${REPO:-esser-ventilation-audit}"
VISIBILITY="${VISIBILITY:-public}"     # set VISIBILITY=private to keep it closed

echo "Target: github.com/${OWNER}/${REPO}  (${VISIBILITY})"
echo

# --- sanity: the large public source files must not be committed -------------
if git ls-files --error-unmatch data/raw/epa_tri_national.csv >/dev/null 2>&1; then
  echo "Refusing to push: data/raw is tracked. Check .gitignore." >&2
  exit 1
fi

if [ ! -d .git ]; then
  git init -q
  git add -A
  git commit -q -m "ESSER ventilation and industrial air emissions: analysis, manuscript, figures"
fi
git branch -M main

if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  echo "Using the GitHub CLI."
  if gh repo view "${OWNER}/${REPO}" >/dev/null 2>&1; then
    echo "Repository already exists; adding it as a remote."
    git remote remove origin 2>/dev/null || true
    git remote add origin "https://github.com/${OWNER}/${REPO}.git"
    git push -u origin main
  else
    gh repo create "${OWNER}/${REPO}" \
      --"${VISIBILITY}" \
      --source=. \
      --remote=origin \
      --description "Exposure model, federal-record linkage and computation record behind an analysis of ESSER ventilation funding and industrial air emissions at US public schools." \
      --push
  fi
else
  cat <<'EOF'
The GitHub CLI is not installed or not authenticated.

Two options:

  A) Install and authenticate it, then re-run this script:
       brew install gh
       gh auth login

  B) Create an EMPTY repository by hand at https://github.com/new
     (no README, no .gitignore, no licence), then run:

       git remote add origin https://github.com/Shiven-Patel/esser-ventilation-audit.git
       git branch -M main
       git push -u origin main

EOF
  exit 1
fi

echo
echo "Done. Written drafts are excluded by .gitignore and stay out of the repository;"
echo "if you keep a manuscript in docs/, check that it was not pushed."
