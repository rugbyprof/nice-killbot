#!/bin/bash

PORT=/dev/cu.SLAB_USBtoUART

mpremote connect "$PORT" \
    fs cp src/* :