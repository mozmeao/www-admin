#!/bin/bash

set -exo pipefail

if [[ -n "${CI_COMMIT_SHA}" ]]; then
    export GIT_COMMIT="$CI_COMMIT_SHA"
else
    export GIT_COMMIT="$(git rev-parse HEAD)"
fi

if [[ -n "${BRANCH_NAME}" ]]; then
    export GIT_BRANCH="${BRANCH_NAME}"
elif [[ -n "${CI_COMMIT_REF_NAME}" ]]; then
    export GIT_BRANCH="${CI_COMMIT_REF_NAME}"
else
    export GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
fi
GIT_BRANCH_PROCESSED="${GIT_BRANCH}-processed"
OUTPUT_DIR="output"
export GIT_AUTHOR_NAME="MozMEAO Robot"
export GIT_AUTHOR_EMAIL="pmac+github-mozmar-robot@mozilla.com"
export GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME"
export GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL"

case $GIT_BRANCH in
    stage)
        BUCKET=stage
        ;;
    prod)
        BUCKET=prod
        ;;
    *)
        BUCKET=dev
        ;;
esac

git fetch origin
git checkout -f "origin/${GIT_BRANCH_PROCESSED}"
rm -rf content static
mv ${OUTPUT_DIR}/* ./
rm -rf "$OUTPUT_DIR"
git add content static
# can rely on json changes only since image names are hashed
# and will change if image contents change
if git status --porcelain | grep ".json"; then
    git commit -m "Add processed card data for ${GIT_COMMIT}"
    echo "Card data update committed"
    S3_URL="s3://bedrock-${BUCKET}-media/media/contentcards/"
    echo "Syncing to $S3_URL"
    aws s3 sync \
        --acl public-read \
        --cache-control "max-age=315360000, public, immutable" \
        --profile bedrock-media \
        "./static" "${S3_URL}"
    git push github-mozmar-robot:mozmeao/www-admin.git HEAD:${GIT_BRANCH_PROCESSED}
else
    echo "No updates"
fi
