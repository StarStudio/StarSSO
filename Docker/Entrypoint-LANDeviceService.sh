#! /bin/sh

SUPERVISOR_CONF=/etc/LANDevice/supervisor.conf
LANDEV_CONF=/etc/LANDevice/LANDevice.conf

if ! [ -e "$SUPERVISOR_CONF" ]; then
    cp /data/Supervisor-LANDevice.conf "$SUPERVISOR_CONF"
fi

if ! [ -e "$LANDEV_CONF" ]; then
    echo LANDevice.conf not found. 
    echo Try to generate LANDevice.conf

    if [ -z "$REDIS_HOST" ]; then
        echo Environment Variable REDIS_HOST not set.
        echo You must provide Redis setting.
        exit 1
    fi
    
    if [ -z "$REDIS_PORT" ]; then
        export REDIS_PORT=6379
    fi
    
    if [ -z "$REDIS_PUBLISH_PREFIX" ]; then
        export REDIS_PUBLISH_PREFIX=LANDEV_DEFAULT
    fi
    
    if [ -z "$TRACK_INTERVAL" ]; then
        export TRACK_INTERVAL=5    
    fi
    
    if [ -z "$PROBE_TIMEOUT" ]; then
        export PROBE_TIMEOUT=10
    fi
    
    if [ -z "$PROBE_INTERVAL" ]; then
        export PROBE_INTERVAL=30;
    fi
    
    if [ -z "$MONITOR_INTERFACE" ]; then
        echo Environment Variable MONITOR_INTERFACE not set.
        echo You must provide an network interfaces to monitor.
    fi

    envsubst < /data/config-LANDeviceService.py.tmpl >> "$LANDEV_CONF"
fi

supervisord -c "$SUPERVISOR_CONF"
