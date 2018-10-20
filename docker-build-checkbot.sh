PROJECT_ROOT=$(dirname "$0")

source "$PROJECT_ROOT/build-env.sh"

build_sdist_checkbot || exit 1
build_sdist_landevice || exit 1
docker build --network host --build-arg DIST_VERSION=$CHECKBOT_VERSION --build-arg LANDEV_VERSION=$LANDEV_VERSION -f "$PROJECT_ROOT/Docker/Dockerfile-CheckBot" -t checkbot:$CHECKBOT_VERSION "$PROJECT_ROOT"
clean_sdist_checkbot
clean_sdist_landevice
