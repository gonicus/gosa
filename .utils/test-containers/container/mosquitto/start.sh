#!/bin/bash

# Check for base ldif container
echo -n "[MOSQUITTO] checking for configuration: "
if [ -d /provision/mosquitto ]; then
    cp -a /provision/mosquitto/* /etc/mosquitto/conf.d

    if [ "$HTTP_AUTH_HOST" != "" ]; then
        echo -n "configured HTTP_AUTH_HOST, "

        # Split host and optional port
        temp=(${HTTP_AUTH_HOST//:/ })
        HOST=${temp[0]}
        PORT=${temp[1]:-8000}

        # Hostname or IP?
        if [[ ! $IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            IP=$(getent hosts $HOST | cut -d\  -f1 | head -n1)

            # Wait until the name resolves
            while [ -z "$IP" ]; do
                sleep .5
                echo -n "."
                IP=$(getent hosts $HOST | cut -d\  -f1 | head -n1)
            done
        fi

        for cfg in /etc/mosquitto/conf.d/*.conf; do
            sed -i "s/%HOST_IP%/$IP/" $cfg
            sed -i "s/%HOST_PORT%/$PORT/" $cfg
        done
    fi

    echo "provisioned"
else
    echo "not found"
fi

exec /usr/sbin/mosquitto -v -c /etc/mosquitto/mosquitto.conf
