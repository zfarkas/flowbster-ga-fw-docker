#!/bin/sh

V=`cat data.txt`

sleep $V

R=$((V/2))

echo "$R" > result.txt
