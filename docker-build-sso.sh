PROJECT_ROOT=$(dirname "$0")

source "$PROJECT_ROOT/build-env.sh"

build_sdist_sso || exit 1
#build_sdist_landevice || exit 1
docker build --network host --build-arg DIST_VERSION=$VERSION -f "$PROJECT_ROOT/Docker/apiserver/Dockerfile" -t starsso:$VERSION "$PROJECT_ROOT" 

#clean_sdist_sso
#clean_sdist_landevice
