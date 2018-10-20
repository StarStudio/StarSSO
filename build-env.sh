PROJECT_ROOT=$(dirname "$0")
VERSION=$(cat "$PROJECT_ROOT/VERSION")
LANDEV_VERSION=$(cat "$PROJECT_ROOT/VERSION-LANDevice")
CHECKBOT_VERSION=$(cat "$PROJECT_ROOT/VERSION-CheckBot")

BUILD_ENV_IMAGE_NAME="python:3.6.6-alpine3.7"

build_sdist_sso() {
    if [ -e $PROJECT_ROOT/dist/StarSSO.tar.gz ]; then
        return 0
    fi

    pushd "$PROJECT_ROOT" >> /dev/null
    docker run -it -v "$(pwd):/data/" "$BUILD_ENV_IMAGE_NAME" sh -c 'cd /data/ && python setup.py sdist'
    BUILD_FAIL=$?
    popd >> /dev/null
    if ! [ $BUILD_FAIL -eq 0 ]; then
        return $BUILD_FAIL
    fi
    mv "$PROJECT_ROOT/dist/StarSSO-$VERSION.tar.gz" "$PROJECT_ROOT/dist/StarSSO.tar.gz"
}

build_sdist_landevice() {
    if [ -e $PROJECT_ROOT/dist/LANDevice.tar.gz ]; then
        return 0
    fi

    pushd "$PROJECT_ROOT" >> /dev/null
    docker run -it -v "$(pwd):/data/" "$BUILD_ENV_IMAGE_NAME" sh -c 'cd /data/ && python setup-landevice.py sdist'
    BUILD_FAIL=$?
    popd >> /dev/null
    if ! [ $BUILD_FAIL -eq 0 ]; then
        return $BUILD_FAIL
    fi
    mv "$PROJECT_ROOT/dist/LANDevice-$LANDEV_VERSION.tar.gz" "$PROJECT_ROOT/dist/LANDevice.tar.gz"
}

build_sdist_checkbot() {
    if [ -e $PROJECT_ROOT/dist/CheckBot.tar.gz ]; then
        return 0
    fi

    pushd "$PROJECT_ROOT" >> /dev/null
    docker run -it -v "$(pwd):/data/" "$BUILD_ENV_IMAGE_NAME" sh -c 'cd /data/ && python setup-checkbot.py sdist'
    BUILD_FAIL=$?
    popd >> /dev/null
    if ! [ $BUILD_FAIL -eq 0 ]; then
        return $BUILD_FAIL
    fi
    mv "$PROJECT_ROOT/dist/CheckBot-$LANDEV_VERSION.tar.gz" "$PROJECT_ROOT/dist/CheckBot.tar.gz"
}


clean_sdist_sso() {
    rm "$PROJECT_ROOT/dist/StarSSO.tar.gz"
}

clean_sdist_landevice() {
    rm "$PROJECT_ROOT/dist/LANDevice.tar.gz"
}

clean_sdist_checkbot() {
    rm "$PROJECT_ROOT/dist/CheckBot.tar.gz"
}

