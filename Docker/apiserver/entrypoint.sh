#! /bin/bash

CONF_PATH=/etc/starsso/apiserver.yml

source /env_default.sh

ERRORS=(
    'You must provide MySQL Host.\n'
    'You must provide Database Name.\n'
    'You must provide MySQL Username\n'
    'You must specified URL root of API\n'
)

VARS=(
    'SSO_MYSQL_HOST,False,Public,'
    'SSO_MYSQL_DB,False,Public,'
    'SSO_MYSQL_USER,False,Public,'
    'SSO_API_HOST,False,Public,'
    'SSO_REDIS_HOST,False,Public,redis'
    'SSO_MYSQL_PORT,True,Public,3306'
    'SSO_MYSQL_PASSWORD,True,Private,null'
    'SSO_MYSQL_CHARSET,True,Public,utf8'
    'SSO_REDIS_PORT,True,Public,6379'
    'SSO_REDIS_PREFIX,True,Public,STARSSO_'
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
