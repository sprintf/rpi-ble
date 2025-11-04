#!/bin/bash

# add this launch script to ~/.bashrc (and remove the --test-mode)
# a command like this should work
source venv/bin/activate
python -m rpi_ble.main
