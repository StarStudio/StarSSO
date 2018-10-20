#! /bin/bash

BASE_CONF=/etc/CheckBot
SUPERVISOR_CONF=$BASE_CONF/supervisor.conf
CONF=$BASE_CONF/CheckBot.conf

ERRORS=(
    'You must provide Redis setting.\n'
    'You must provide MySQL Host.\n'
    'You must provide Database Name.\n'
    'You must provide MySQL Username\n'
)

VARS=(
    'REDIS_HOST,False,Public,localhost'
    'MYSQL_HOST,False,Public,localhost'
    'MYSQL_DB,False,Public,starstudio'
    'MYSQL_USER,False,Public,root'
    'REDIS_PORT,True,Public,6379'
    'ACCESS_LOG,True,Public,/var/log/access.log'
    'ERROR_LOG,True,Public,/var/log/error.log'
    'DEBUG_LOG,True,Public,/var/log/debug.log'
    'MYSQL_PORT,True,Public,3306'
    'MYSQL_PASSWORD,True,Private,'
    'MYSQL_CHARSET,True,Public,utf8'
    'LAN_DEV_PREFIX,True,Public,LANDEV_DEFAULT'
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
    if [ -z "$MYSQL_PASSWORD" ]; then
        export MYSQL_PASSWORD=None
    else
        export MYSQL_PASSWORD=\'$MYSQL_PASSWORD\'
    fi
}

if ! [ -e "$SUPERVISOR_CONF" ]; then
    cp /data/Supervisor-CheckBot.conf "$SUPERVISOR_CONF"
fi


if ! [ -e "$CONF" ]; then
    echo $CONF not found.
    echo Try to generate $CONF
    echo ''

    environ_set_default
    post_process_variables
    print_setting
    envsubst < /data/config-CheckBot.py.tmpl >> "$CONF"
fi

supervisord -c "$SUPERVISOR_CONF"
