FROM python:3.6.6-alpine3.7

RUN set -xe;\
    echo [easy_install] >> ~/.pydistutils.cfg ;\
    echo index-url=https://pypi.tuna.tsinghua.edu.cn/simple >> ~/.pydistutils.cfg; \
    sed -Ei "s/dl-cdn\.alpinelinux\.org/mirrors.tuna.tsinghua.edu.cn/g" /etc/apk/repositories; \
    mkdir /apk-cache; \
    apk add tzdata gettext py-cffi bash libffi-dev openssl-dev musl-dev --cache-dir /apk-cache; \
    rm -rf /apk-cache; \
    rm /etc/localtime; \
    ln -s /usr/share/zoneinfo/Asia/Shanghai /etc/localtime
    
ARG DIST_VERSION

COPY ./dist/StarSSO.tar.gz /docker-build/

RUN set -xe;\
    mkdir /apk-cache; \
    apk add gcc g++ linux-headers --cache-dir /apk-cache -t build-deps; \
    cd /docker-build; \
    tar -xvzf StarSSO.tar.gz ;\
    cd /docker-build/StarSSO-$DIST_VERSION; \
    python ./setup.py install; \
    apk del build-deps; \
    rm -rf /apk-cache; \
    rm -rf /docker-build; \
    mkdir /etc/starsso; \
    mkdir /var/log/starsso

COPY ./Docker/env_default.sh /env_default.sh
COPY ./Docker/apiserver/entrypoint.sh /entrypoint.sh
COPY ./Docker/apiserver/entrypoint-agent.sh /entrypoint-agent.sh
COPY ./Docker/apiserver/entrypoint-apiserver.sh /entrypoint-apiserver.sh
COPY ./Docker/apiserver/apiserver.yml.tmpl /data/apiserver.yml.tmpl
COPY ./Docker/apiserver/agent.yml.tmpl /data/agent.yml.tmpl


RUN set -xe; \
    chmod a+x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
