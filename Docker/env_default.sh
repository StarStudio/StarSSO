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

