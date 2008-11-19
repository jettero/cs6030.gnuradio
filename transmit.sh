#!/bin/bash

file=$1; shift
[ -z "$file" ] && file=gmsk_to_file.py

if [ ! -f "$file" ]; then
    echo file?
    exit 1
fi

while [ true ]; do
    echo sending
    ./file_to_gmsk.py $* --dsp $file

    echo sleeping for 5 seconds
    sleep 5
done
