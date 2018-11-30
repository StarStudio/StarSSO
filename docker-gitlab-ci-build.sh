IMAGE_REF_NAME=$CI_REGISTRY_IMAGE
COMMIT_IMAGE_ID=$(echo $CI_COMMIT_SHA | sed -E 's/(([A-Z]|[a-z]|[0-9]){10}).*/\1/')

if ! [ -z "$CI_COMMIT_TAG" ]; then
    IMAGE_REF_NAME=$IMAGE_REF_NAME/publish:$CI_COMMIT_TAG
else
    IMAGE_REF_NAME=$IMAGE_REF_NAME/$CI_COMMIT_REF_NAME:$COMMIT_IMAGE_ID
fi

./docker-build.sh "$IMAGE_REF_NAME"

docker login -u gitlab-ci-token -p $CI_JOB_TOKEN $CI_REGISTRY
docker push $IMAGE_REF_NAME
