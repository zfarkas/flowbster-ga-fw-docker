#!/bin/sh

V=`cat input-data.txt`

case $V in
    ''|*[!0-9]*) exit 1 ;;
    *) echo good ;;
esac

cp input-data.txt output-data.txt
