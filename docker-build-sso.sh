PROJECT_ROOT=$(dirname "$0")

source "$PROJECT_ROOT/build-env.sh"

echo 111
build_sdist_sso || exit 1
build_sdist_landevice || exit 1
docker build --network host --build-arg DIST_VERSION=$VERSION --build-arg LANDEV_DIST_VERSION=$LANDEV_VERSION -f "$PROJECT_ROOT/Docker/Dockerfile-SSO" -t starsso:$VERSION "$PROJECT_ROOT" 

clean_sdist_sso
clean_sdist_landevice
