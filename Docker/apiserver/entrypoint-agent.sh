#! /bin/bash

CONF_PATH=/etc/starsso/apiserver.yml

source /env_default.sh

ERRORS=(
    'You must provide API Root.\n'
    'You must provide interface.\n'
    'You must provide net token\n'
)

VARS=(
    'SSO_API_HOST,False,Public,'
    'SSO_PROBE_INTERFACE,False,Public,'
    'SSO_NET_TOKEN,False,Public,'
    'SSO_LISTEN,True,Public,0.0.0.0'
    'SSO_PORT,True,Public,80'
)

if ! [ -e "$CONF_PATH" ]; then
    echo $CONF_PATH not found.
    echo Try to generate $CONF_PATH
    echo ''

    environ_set_default
    print_setting
    envsubst < /data/apiserver.yml.tmpl >> "$CONF_PATH"
fi

starsso-server $*
