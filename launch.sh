#!/bin/bash

# add this launch script to ~/.bashrc (and remove the --test-mode)
# a command like this should work
# (cd /home/pi/rpi-ble; ./launch.sh)
source venv/bin/activate
python -m rpi_ble.main
