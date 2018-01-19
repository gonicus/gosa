#!/bin/bash

# Check for base ldif container
echo -n "[SLAPD] checking for base configuration: "
if [ ! -f /var/lib/ldap/data.mdb ]; then
    if [ -f /provision/base.ldif ]; then
        cp /usr/share/doc/slapd/examples/DB_CONFIG /var/lib/ldap/DB_CONFIG

        slapadd -q -l /provision/base.ldif -b dc=example,dc=net &> /tmp/slapadd.log
        if [ $? -ne 0 ]; then
            echo "failed\n\n"
            cat /tmp/slapadd.log
        else
            echo "provisioned"
        fi
    else
        echo "missing"
    fi
else
    echo "found"
fi

chown -R $LDAP_USER:$LDAP_GROUP /var/lib/ldap
exec /usr/sbin/slapd -u openldap -d 256
