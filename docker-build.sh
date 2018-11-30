PROJECT_ROOT=$(dirname "$0")

source "$PROJECT_ROOT/build-env.sh"

if [ -z "$1" ]; then
    IMAGE_REF_NAME=starsso:$VERSION
else
    IMAGE_REF_NAME=$1
fi

build_sdist_sso || exit 1
#build_sdist_landevice || exit 1
docker build --network host --build-arg DIST_VERSION=$VERSION -f "$PROJECT_ROOT/Docker/apiserver/Dockerfile" -t "$IMAGE_REF_NAME"  "$PROJECT_ROOT" 

#clean_sdist_sso
#clean_sdist_landevice
