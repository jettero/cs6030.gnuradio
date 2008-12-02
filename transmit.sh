#!/bin/bash

file=$1; shift
[ -z "$file" ] && file=modulate_file.py

if [ ! -f "$file" ]; then
    echo file?
    exit 1
fi

while [ true ]; do
    echo sending

    # the softrock rxtx is 5k off from the lite, so -2999 is actually 7001
    ./modulate_file.py -c -2999 --dsp $file

    echo sleeping for 2 seconds
    sleep 2
done
