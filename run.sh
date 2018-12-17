#!/bin/bash

set -exo pipefail

IMAGE_NAME="${DOCKER_IMAGE_NAME:-www-admin-image-processor}"
IMAGE_NAME="${IMAGE_NAME}:$(git rev-parse HEAD)"
TMP_DIR="tmp_static"
GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
GIT_BRANCH_PROCESSED="${GIT_BRANCH}-processed"

if [[ "$GIT_BRANCH" == "master" ]]; then
    BUCKETS=(dev)
elif [[ "$GIT_BRANCH" == "prod" ]]; then
    BUCKETS=(stage prod)
else
    # nothing to do
    echo "No matching branch. Nothing to do."
    exit 1
fi

function imageExists() {
    docker history -q "${IMAGE_NAME}" > /dev/null 2>&1
    return $?
}

if ! imageExists; then
    docker build -t "$IMAGE_NAME" --pull .
fi

rm -rf "${TMP_DIR}" && mkdir "${TMP_DIR}"
docker run --rm -u "$(id -u)" -v "$PWD:/app" "$IMAGE_NAME"

for BUCKET in "${BUCKETS[@]}"; do
    S3_URL="s3://bedrock-${BUCKET}-media/media/contentcards/"
    echo "Syncing to $S3_URL"
    aws s3 sync \
        --acl public-read \
        --cache-control "max-age=315360000, public, immutable" \
        --profile bedrock-media \
        "./${TMP_DIR}" "${S3_URL}"
done

if [[ "$1" == "commit" ]]; then
    if git status --porcelain | grep -E "\.md$"; then
        git branch -D "${GIT_BRANCH_PROCESSED}" || true
        git checkout -b "${GIT_BRANCH_PROCESSED}"
        git add ./content/
        git commit -m "Update card data with hashed image names"
        echo "Card data update committed"
    else
        echo "No updates"
    fi
fi

if [[ -n "$SNITCH_URL" ]]; then
    curl "$SNITCH_URL"
fi
