#!/bin/bash

set -exo pipefail

# store slack-notify.sh for when we switch branches later
cp ./slack-notify.sh ../

export GIT_COMMIT="$(git rev-parse HEAD)"
export GIT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
GIT_BRANCH_PROCESSED="${GIT_BRANCH}-processed"
IMAGE_NAME="${DOCKER_IMAGE_NAME:-www-admin-image-processor}"
IMAGE_NAME="${IMAGE_NAME}:${GIT_COMMIT}"
OUTPUT_DIR="output"

if [[ "$GIT_BRANCH" == "master" ]]; then
    BUCKET="dev"
elif [[ "$GIT_BRANCH" == "stage" ]]; then
    BUCKET="stage"
elif [[ "$GIT_BRANCH" == "prod" ]]; then
    BUCKET="prod"
else
    # nothing to do
    echo "No matching branch. Nothing to do."
    exit 1
fi

../slack-notify.sh --stage "Content card update" --status starting

function imageExists() {
    docker history -q "${IMAGE_NAME}" > /dev/null 2>&1
    return $?
}

if ! imageExists; then
    docker build -t "$IMAGE_NAME" --pull .
fi

docker run --rm -u "$(id -u)" -v "$PWD:/app" "$IMAGE_NAME"

if [[ "$1" == "commit" ]]; then
    git fetch origin
    git checkout -f "origin/${GIT_BRANCH_PROCESSED}"
    rm -rf content static
    mv ${OUTPUT_DIR}/* ./
    rm -rf "$OUTPUT_DIR"
    if git status --porcelain | grep ".json"; then
        git add .
        git commit -m "Add processed card data for ${GIT_COMMIT}"
        echo "Card data update committed"
        S3_URL="s3://bedrock-${BUCKET}-media/media/contentcards/"
        echo "Syncing to $S3_URL"
        aws s3 sync \
            --acl public-read \
            --cache-control "max-age=315360000, public, immutable" \
            --profile bedrock-media \
            "./static" "${S3_URL}"
        ../slack-notify.sh --stage "Content card update" --status shipped
    else
        echo "No updates"
        ../slack-notify.sh --stage "Nothing changed" --status success
    fi
fi

if [[ -n "$SNITCH_URL" ]]; then
    curl "$SNITCH_URL"
fi
