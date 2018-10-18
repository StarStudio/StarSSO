PROJECT_ROOT=$(dirname "$0")
source "$PROJECT_ROOT/build-env.sh"

build_sdist_landevice
docker build --network host --build-arg DIST_VERSION=$LANDEV_VERSION -f "$PROJECT_ROOT/Docker/Dockerfile-LANDeviceService" -t landevice:$LANDEV_VERSION "$PROJECT_ROOT"
clean_sdist_landevice
