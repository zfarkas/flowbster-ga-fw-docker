#!/bin/sh

V=`cat data.txt`

R=$((V-1))

echo "$R" > result.txt
