#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage: $0 <percentage>"
    echo "Example: $0 50"
    exit 1
fi

PERCENTAGE=$1

docker exec z35_pclient_zad_12 tc qdisc add dev eth0 root netem loss ${PERCENTAGE}%
