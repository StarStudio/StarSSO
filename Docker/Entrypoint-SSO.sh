#! /bin/bash

SUPERVISOR_CONF=/etc/StarSSO/supervisor.conf
SSO_CONF=/etc/StarSSO/SSO.conf
GUNICORN_CONF=/etc/StarSSO/gunicorn.py

ERRORS=(
    'You must provide Redis setting.\n'
    'You must provide MySQL Host.\n'
    'You must provide Database Name.\n'
    'You must provide MySQL Username\n'
    'Host name must be set to Hostname part in URL.\n'
)

VARS=(
    'REDIS_HOST,False,Public,localhost'
    'MYSQL_HOST,False,Public,localhost'
    'MYSQL_DB,False,Public,starstudio'
    'MYSQL_USER,False,Public,root'
    'SERVER_HOST_NAME,False,Public,localhost'
    'REDIS_PORT,True,Public,6379'
    'ACCESS_LOG,True,Public,/var/log/access.log'
    'ERROR_LOG,True,Public,/var/log/error.log'
    'DEBUG_LOG,True,Public,/var/log/debug.log'
    'SECRET_KEY_FILE,True,Public,/etc/StarSSO/jwt.pri'
    'SECRET_KEY_FILE_MODE,True,Public,600'
    'PUBLIC_KEY_FILE,True,Public,/etc/StarSSO/jwt.pub'
    'PUBLIC_KEY_MODE,True,Public,666'
    'SALT_FILE,True,Public,/etc/StarSSO/starstudio.salt'
    'SALT_FILE_MODE,True,Public,600'
    'AUTH_TOKEN_EXPIRE_DEFAULT,True,Public,86400'
    'APP_TOKEN_EXPIRE_DEFAULT,True,Public,86400'          
    'MYSQL_PORT,True,Public,3306'
    'MYSQL_PASSWORD,True,Private,'
    'MYSQL_CHARSET,True,Public,utf8'
    'ALLOW_REGISTER,True,Public,True'
    'ALLOW_ANONYMOUS_GROUP_INFO,True,Public,True'
    'USER_INITIAL_ACCESS,True,Public,auth read_self read_internal read_other read_group write_self'
    'APP_INITIAL_ACCESS,True,Public,auth read_self'
    'LAN_DEV_PREFIX,True,Public,LANDEV_DEFAULT'
    'HTTP_PROTOCOL,True,Public,http'
)

environ_set_default() {
    declare -i var_count=${#VARS[@]}-1
    for i in $(seq 0 1 $var_count); do
        var_item="${VARS[$i]}"
        var_name=$(echo "$var_item" | cut -d ',' -f 1)
        allow_default=$(echo "$var_item" | cut -d ',' -f 2)
        default_value=$(echo "$var_item" | cut -d ',' -f 4)

        if [ "$allow_default" = 'False' ]; then
            if [ -z "$(eval echo \$$var_name)" ]; then
                echo Environment Variable $var_name not set.
                echo -en ${ERRORS[$i]}
                exit 1
            fi
        elif [ "$allow_default" = 'True' ]; then
            if [ -z "$(eval echo \$$var_name)" ]; then
                eval export "\"\$var_name=$default_value\""
            fi
        else
            echo Variable definition table has wrong configure value.
            echo AllowDefault cannot be $allow_default for $var_name
        fi
    done
}

print_setting() {
    echo Configure:
    declare -i var_count=${#VARS[@]}-1
    for i in $(seq 0 1 $var_count); do
        var_item=${VARS[$i]}
        var_name=$(echo "$var_item" | cut -d ',' -f 1)
        is_secret=$(echo "$var_item" | cut -d ',' -f 3)
        echo -n '    '
        if [ "$is_secret" = 'Public' ]; then
            eval echo $var_name=\$$var_name
        elif [ "$is_secret" = 'Private' ]; then
            echo -n $var_name=
            echo $(eval echo \$$var_name) | sed 's/./*/g'
        else
            echo Variable definition table has wrong configure value.
            echo IsSecret cannot be $is_secret for $var_name
        fi
    done
}

post_process_variables() {
    USER_INITIAL_ACCESS=frozenset\(\[\"$(echo $USER_INITIAL_ACCESS | sed -E 's/\s/","/g')\"\]\)
    APP_INITIAL_ACCESS=frozenset\(\[\"$(echo $APP_INITIAL_ACCESS | sed -E 's/\s/","/g')\"\]\)
    export SSO_WEB_REDIRECT_PREFIX="$HTTP_PROTOCOL://$SERVER_HOST_NAME"
    if ! [ "$HTTP_PROTOCOL" = 'https' ]; then
        echo Current protocol is $HTTP_PROTOCOL. Use HTTPS is recommanded.
    fi
    if [ -z "$MYSQL_PASSWORD" ]; then
        export MYSQL_PASSWORD=None
    else
        export MYSQL_PASSWORD=\'$MYSQL_PASSWORD\'
    fi
}

if ! [ -e "$SUPERVISOR_CONF" ]; then
    cp /data/Supervisor-SSO.conf "$SUPERVISOR_CONF"
fi

if ! [ -e "$GUNICORN_CONF" ]; then
    cp /data/gunicorn.py "$GUNICORN_CONF"
fi

if ! [ -e "$SSO_CONF" ]; then
    echo $SSO_CONF not found.
    echo Try to generate $SSO_CONF
    echo ''

    environ_set_default
    post_process_variables
    print_setting
    envsubst < /data/config-SSO.py.tmpl >> "$SSO_CONF"
fi

supervisord -c "$SUPERVISOR_CONF"
