#!/bin/bash

./demodulate_file.py --dsp --exit-on-receive

if [ -f test_modulate_file.py ]; then
    echo
    echo "received file test_modulate_file.py, apparently"
    echo "comparing"

    md5sum modulate_file.py test_modulate_file.py
    echo
    echo "press enter to exit"
    read X
fi
