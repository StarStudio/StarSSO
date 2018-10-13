PROJECT_ROOT=$(dirname "$0")
VERSION=$(cat "$PROJECT_ROOT/VERSION")
LANDEV_VERSION=$(cat "$PROJECT_ROOT/VERSION-LANDevice")

python "$PROJECT_ROOT/setup.py" sdist || exit 1
python "$PROJECT_ROOT/setup-landevice.py" sdist || exit 1
mv "$PROJECT_ROOT/dist/StarSSO-$VERSION.tar.gz" "$PROJECT_ROOT/dist/StarSSO.tar.gz"
mv "$PROJECT_ROOT/dist/LANDevice-$VERSION.tar.gz" "$PROJECT_ROOT/dist/LANDevice.tar.gz"

docker build --build-arg DIST_VERSION=$VERSION --build-arg LANDEV_DIST_VERSION=$LANDEV_VERSION -f "$PROJECT_ROOT/Docker/Dockerfile-SSO" -t starsso:$VERSION "$PROJECT_ROOT"
rm "$PROJECT_ROOT/dist/StarSSO.tar.gz"
rm "$PROJECT_ROOT/dist/LANDevice.tar.gz"
