PROJECT_ROOT=$(dirname "$0")
VERSION=$(cat "$PROJECT_ROOT/VERSION-LANDevice")

python "$PROJECT_ROOT/setup-landevice.py" sdist || exit 1
mv "$PROJECT_ROOT/dist/LANDevice-$VERSION.tar.gz" "$PROJECT_ROOT/dist/LANDevice.tar.gz"

docker build --build-arg DIST_VERSION=$VERSION -f "$PROJECT_ROOT/Docker/Dockerfile-LANDeviceService" -t landevice:$VERSION "$PROJECT_ROOT"
rm "$PROJECT_ROOT/dist/LANDevice.tar.gz"
