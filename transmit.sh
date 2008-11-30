#!/bin/bash

file=$1; shift
[ -z "$file" ] && file=modulate_file.py

if [ ! -f "$file" ]; then
    echo file?
    exit 1
fi

while [ true ]; do
    echo sending
    ./modulate_file.py $* --dsp $file

    echo sleeping for 5 seconds
    sleep 5
done
