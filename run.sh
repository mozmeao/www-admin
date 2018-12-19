#!/bin/bash

set -exo pipefail

IMAGE_NAME="${DOCKER_IMAGE_NAME:-www-admin-image-processor}"
IMAGE_NAME="${IMAGE_NAME}:$(git rev-parse HEAD)"
OUTPUT_DIR="output"
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

docker run --rm -u "$(id -u)" -v "$PWD:/app" "$IMAGE_NAME"

if [[ "$1" == "commit" ]]; then

    for BUCKET in "${BUCKETS[@]}"; do
        S3_URL="s3://bedrock-${BUCKET}-media/media/contentcards/"
        echo "Syncing to $S3_URL"
#        aws s3 sync \
#            --acl public-read \
#            --cache-control "max-age=315360000, public, immutable" \
#            --profile bedrock-media \
#            "./${OUTPUT_DIR}/static" "${S3_URL}"
    done

    git branch -D "${GIT_BRANCH_PROCESSED}" || true
    git fetch origin
    git checkout "${GIT_BRANCH_PROCESSED}"
    rm -rf content static
    mv ${OUTPUT_DIR}/* ./
    rm -rf "$OUTPUT_DIR"
    if git status --porcelain | grep content; then
        git add .
        git commit -m "Add processed card data"
        echo "Card data update committed"
    else
        echo "No updates"
    fi
fi

if [[ -n "$SNITCH_URL" ]]; then
    curl "$SNITCH_URL"
fi
