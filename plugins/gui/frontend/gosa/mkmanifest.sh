#!/bin/bash

DATE=$(LANG=C date)
CACHE=$(find -type f | grep -v cache.manifest | cut -b3-)

cat <<EOF
CACHE MANIFEST
# Manifest generated on $DATE

CACHE:
$CACHE

NETWORK:
*

EOF
