#! /bin/bash

is_agent_mode() {
    while true; do
        if [ -z "$1" ]; then 
            break;
        fi
        if [ "$1" == '--agent' ]; then
            return 0
        fi
        shift
    done
    return 1
}

if is_agent_mode $*; then
    exec /entrypoint-agent.sh $*
else
    exec /entrypoint-apiserver.sh $*
fi
